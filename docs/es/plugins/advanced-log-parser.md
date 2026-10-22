# Advanced Log Parser

*Última actualización del artículo: 2026-09-16.*

## Qué hace

Advanced Log Parser monitoriza ficheros de log desde Pandora FMS. En cada ejecución recorre un directorio, selecciona ficheros por nombre y líneas por contenido mediante expresiones regulares, e imprime las líneas coincidentes como entradas `log_module` de Pandora FMS en la salida estándar.

El plugin lee cada fichero de log de forma incremental. Mantiene un índice por fichero de log y por tipo de origen, de modo que cada ejecución captura solo las líneas escritas desde la ejecución anterior en lugar de todo el fichero. Las líneas capturadas se codifican en Base64, lo que mantiene válido el XML generado sea cual sea el contenido del log.

El plugin se ejecuta como plugin de agente de Pandora FMS (`module_plugin`) y también puede ejecutarse manualmente. No crea ningún agente propio: los módulos de log que emite pertenecen al agente que lo ejecuta.

## Preparación

### Compatibilidad

| Sistemas donde se ha probado | Rocky 9; Windows 11 con el agente Windows de Pandora FMS |
| --- | --- |
| Sistemas donde funciona | Cualquier sistema Linux soportado por Pandora FMS |

### Requisitos

- Acceso de lectura al directorio analizado y a los ficheros de log que contiene.
- Acceso de lectura y escritura al directorio de índices. Por defecto el plugin usa el directorio temporal del sistema operativo: `/tmp` en la mayoría de sistemas Linux, o la ruta indicada en `TMPDIR` cuando esa variable está definida.
- El usuario que ejecuta el plugin debe disponer de esos permisos, ya que el agente ejecuta el plugin con su propio usuario.

### Instalación

El plugin se distribuye como un único binario. Hay dos vías de despliegue disponibles.

**Subida manual** — copie el binario al directorio de plugins del agente Pandora FMS y dele permisos de ejecución. En Linux el directorio de plugins del agente es `/etc/pandora/plugins` y en Windows es `%ProgramFiles%\pandora_agent\util`.

**Colecciones** — despliegue el mismo binario en muchos agentes a la vez desde la consola de Pandora FMS. Esta vía requiere:

- La configuración remota activada en el agente, que solo está disponible con el modo de transferencia Tentacle.
- El comando `unzip` en el agente. Cada colección se transfiere como un fichero ZIP y el agente la descomprime localmente.

Cree la colección en **Configuration → Collections**, añada el binario a ella y asigne la colección a cada agente desde la pestaña **Collection** del agente. El agente descomprime la colección en un directorio con el nombre corto de la colección, así que el binario no queda en el directorio de plugins:

| Plataforma | Ruta del binario en el agente |
| --- | --- |
| Linux | `/etc/pandora/collections/<nombre-corto>/pandora_logparser` |
| Windows | `%ProgramFiles%\pandora_agent\collections\<nombre-corto>\pandora_logparser.exe` |

En Linux `/etc/pandora/collections` es el mismo directorio que `/usr/share/pandora_agent/collections`.

Como la ruta lleva el nombre corto, la línea `module_plugin` debe usar la ruta completa:

```
module_plugin /etc/pandora/collections/<nombre-corto>/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --idx-dir /var/tmp/pandora-logparser
```

La consola mantiene cada colección sincronizada mediante un hash MD5: cuando la colección cambia en la consola, el agente reemplaza su copia y descarta cualquier modificación local. Con la configuración remota activada, el agente también sobrescribe su `pandora_agent.conf` local con la configuración almacenada en la consola, así que registre el módulo desde la consola en lugar de editar el fichero en el agente.

## Configuración

### Registrar el plugin en el agente

Añada un bloque `module_plugin` al fichero de configuración del agente. El agente ejecuta el plugin en cada intervalo del agente y asocia a sí mismo los módulos de log emitidos:

```
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error|critical' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
module_end
```

El bloque no necesita `module_name`: el plugin genera sus propios módulos y el agente los añade tal cual, así que un nombre ahí no daría nombre a nada de lo que se ve en la consola. El agente solo lo usa en sus propios mensajes de log, y lo deriva cuando la directiva no está.

La primera ejecución no produce datos: el plugin registra cada fichero coincidente en su final actual. Las ejecuciones posteriores capturan únicamente las líneas nuevas que coinciden.

Entrecomille siempre las opciones que contengan `*`, `?`, `|` u otros metacaracteres del shell, por ejemplo `'.+\.log'` o `'(?i)error'`, para que el shell no las expanda. Ese entrecomillado es del shell de Linux; el agente de Windows ejecuta el comando a través de `cmd.exe`, donde las reglas son distintas. Consulte [Windows: valores no ASCII y metacaracteres del shell](#windows-valores-no-ascii-y-metacaracteres-del-shell).

### Índices y el tipo de origen

Cada fichero de log tiene un índice por tipo de origen. El valor de `--source-type` forma parte de la identidad de ese índice, lo que tiene tres consecuencias:

- Dos módulos que lean el mismo fichero de log deben usar valores distintos de `--source-type`. Si lo comparten, comparten el índice y solo el módulo que se ejecuta primero ve las líneas nuevas.
- Cambiar el `--source-type` de un módulo existente hace que ese módulo vuelva a empezar al final del fichero. Todo lo escrito desde la última ejecución del tipo de origen anterior se omite.
- El campo `source` de los módulos de log generados lleva el valor de `--source-type` tal cual, de modo que también identifica el origen de los datos en Pandora FMS.

No reutilice un valor de `--source-type` para otro fichero de log y otra combinación de filtros salvo que quiera compartir la posición de lectura.

### Varios módulos sobre los mismos ficheros

Defina un bloque `module_plugin` por filtro y asigne a cada bloque su propio `--source-type`:

```
# Módulo para errores
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
module_end

# Módulo para avisos
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)warn' --source-type app_warnings --idx-dir /var/tmp/pandora-logparser
module_end
```

### Fichero de configuración

Use `--config <ruta>` para leer las opciones de un fichero UTF-8 en lugar de la línea de comandos, o además de ella:

```
dir = /var/log/myapp
name_regex = .+\.log
content_regex = (?i)error
source_type = app_errors
idx_dir = /var/tmp/pandora-logparser
```

Formato del fichero:

- Una línea `clave = valor`. Las claves válidas son `dir`, `name_regex`, `content_regex`, `content_regex_base64`, `source_type`, `idx_dir` y `max_line_bytes`.
- Los espacios alrededor de `=` se ignoran y el valor se recorta. Un patrón que deba empezar o terminar con un espacio usa la secuencia de escape `\x20`.
- `#` inicia un comentario solo al principio de la línea, por lo que un valor puede contener `#`. Las líneas en blanco se ignoran.
- Se aceptan un BOM UTF-8 y finales de línea CR/LF.
- El fichero puede ser parcial: una clave que no aparece conserva su valor por defecto.
- Una clave desconocida, una clave duplicada, un valor vacío o una línea sin `=` son errores y detienen la ejecución. La clave `config` se rechaza porque no se admite la recursión.
- El fichero de configuración no debe superar los 4 MiB.

Precedencia:

- Una opción indicada explícitamente en la línea de comandos prevalece clave por clave sobre el valor del fichero. Un `--name-regex '.*'` explícito sigue siendo una elección explícita.
- El filtro de contenido se resuelve como un grupo. Cuando la línea de comandos proporciona `--content-regex` o `--content-regex-base64`, las claves `content_regex` y `content_regex_base64` del fichero se ignoran por completo.
- Dos fuentes del filtro de contenido en la misma capa son un error: dos opciones de línea de comandos, o bien `content_regex` y `content_regex_base64` en el fichero.
- Sin ninguna fuente se aplica el valor por defecto `.*`. Al menos una fuente de opciones debe proporcionar `dir`.

### Windows: valores no ASCII y metacaracteres del shell

El plugin no tiene ningún problema de codificación propio. En Windows, Go lee la línea de comandos a través de la API de caracteres anchos y la convierte a UTF-8, y el plugin lee los ficheros de log y los ficheros de configuración como UTF-8. La corrupción ocurre antes de que el plugin arranque.

El agente de Windows ejecuta cada `module_plugin` como `cmd.exe /c "<comando>"` y convierte la línea de comandos de UTF-8 a la página de códigos ANSI del sistema. El texto no ASCII no sobrevive a esa conversión, de modo que el plugin nunca recibe el texto que usted escribió.

Los dos modos de fallo no son igual de visibles:

| Valor | Síntoma |
| --- | --- |
| `dir` | La ruta no existe después de la conversión. La ejecución falla con estado de salida `1`. |
| `content_regex`, `name_regex` | El patrón compila y no coincide nunca. La ejecución termina bien, no imprime nada y no captura datos. |

El segundo caso es el peligroso: nada falla, así que un patrón no ASCII parece correcto en la configuración mientras no captura nada de forma silenciosa.

#### Metacaracteres de cmd.exe

El comando pasa además por `cmd.exe`, de modo que sus metacaracteres siguen activos. Las comillas simples no son caracteres de entrecomillado para `cmd.exe`, así que nunca protegen un patrón:

```
module_plugin ... --content-regex '(?i)error|critical' ...
```

```
'critical'' is not recognized as an internal or external command
```

Las comillas dobles dentro del patrón sí lo protegen, porque sobreviven a las comillas externas que el agente añade alrededor de todo el comando. `%` es la excepción, porque `cmd.exe` lo expande antes de que arranque el plugin:

| El patrón contiene | Sin comillas | Con comillas dobles |
| --- | --- | --- |
| <code>&#124;</code> | falla, estado de salida `255` | funciona |
| `&` | falla, estado de salida `1` | funciona |
| `<` | falla, estado de salida `1` | funciona |
| `>` | **falla en silencio**, estado de salida `0` | funciona |
| `^` | **falla en silencio**, estado de salida `0` | funciona |
| un `%` aislado | funciona | funciona |
| `%NOMBRE%` | **falla en silencio** | **falla en silencio** |

Un fallo silencioso es el caso peligroso: la ejecución informa de éxito, el plugin recibe un patrón truncado y captura líneas que el patrón que usted escribió nunca casaría. `^` es el ejemplo más claro, porque es el ancla del inicio en patrones como `^ERROR`: sin protección, el ancla desaparece y el patrón coincide en cualquier parte de la línea.

Las dos filas de `%` son coherentes: `cmd.exe` solo expande un nombre entre dos signos de porcentaje, y las comillas dobles no impiden esa expansión.

Solo el fichero de configuración y Base64 evitan todos los casos anteriores. Use uno de ellos siempre que un patrón contenga alguno de estos caracteres.

#### Cómo pasar valores no ASCII

Solo la primera de estas vías sirve para una ruta.

**Fichero de configuración (`--config`)** — la única vía para un `dir` no ASCII. La línea de comandos solo lleva la ruta del fichero, que debe ser ASCII, y los valores de dentro del fichero se leen como UTF-8 desde el disco, así que nunca pasan por la conversión de página de códigos:

```
dir = C:\registros_日本語_Ошибка
content_regex = (?i)error|critical
source_type = app_errors
```

```
module_plugin "%ProgramFiles%\pandora_agent\util\pandora_logparser.exe" --config "C:\ProgramData\PandoraFMS\logparser.conf"
```

**Base64 (`--content-regex-base64`)** — para el patrón de contenido. Base64 es ASCII y no contiene ningún metacaracter del shell, así que evita tanto la página de códigos como `cmd.exe`. Genere el valor a partir de los bytes UTF-8 del patrón:

```bash
printf '%s' 'Ошибка' | base64
```

Ese comando imprime `0J7RiNC40LHQutCw`. En Windows, use PowerShell:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('Ошибка'))
```

**Escapes Unicode (`\x{...}`)** — mantiene la línea de comandos en ASCII sin necesidad de un fichero de configuración. Los resuelve el motor de expresiones regulares de Go, así que son válidos en `--content-regex` y `--name-regex`:

```
--content-regex '\x{041E}\x{0428}\x{0418}\x{0411}\x{041A}\x{0410}'
```

Un escape solo funciona dentro de una expresión regular. No existe ninguna sintaxis de escape para una ruta: `\x{...}` en `--dir` es el nombre de un directorio literal.

#### Lo que no funciona

- Texto no ASCII en la línea de comandos. El agente lo convierte antes de que el plugin arranque, así que `--dir` falla con estado de salida `1` y `--content-regex` falla de forma silenciosa.
- Escribir los valores en la página de códigos ANSI dentro de `pandora_agent.conf`. El agente lee la línea de comandos como UTF-8 y la convierte a ANSI, así que los bytes ANSI ya están corruptos antes de esa conversión.
- Comillas simples alrededor de un patrón que contenga cualquiera de los metacaracteres anteriores. `cmd.exe` no trata las comillas simples como entrecomillado, así que el patrón se parte y la ejecución falla.
- Un patrón que contenga `%NOMBRE%`. `cmd.exe` lo expande antes de que arranque el plugin y las comillas dobles no lo impiden, así que no hay ninguna forma en la línea de comandos que funcione. Use el fichero de configuración.

## Verificación

Confirme que el plugin funciona antes de integrarlo en el agente. El ejemplo usa un directorio nuevo.

1. Cree el fichero de log y ejecute el plugin una vez:

```bash
touch /var/log/myapp/app.log
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
```

La primera ejecución no imprime nada y termina con estado `0`: ha registrado el fichero en su final actual.

2. Añada una línea coincidente:

```bash
printf 'ERROR: disco lleno\n' >> /var/log/myapp/app.log
```

3. Ejecute el plugin de nuevo:

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
```

Ahora imprime una entrada `log_module`:

```xml
<log_module>
  <source><![CDATA[app_errors]]></source>
  <data>&#34;RVJST1I6IGRpc2NvIGxsZW5v&#34;</data>
  <encoding>base64</encoding>
</log_module>
```

4. Decodifique el valor de `data` para confirmar el texto capturado:

```bash
printf 'RVJST1I6IGRpc2NvIGxsZW5v' | base64 -d
```

```
ERROR: disco lleno
```

Una tercera ejecución sin líneas nuevas no imprime nada y termina con estado `0`. Los ficheros sin líneas nuevas coincidentes no producen ninguna entrada, y una ejecución en la que nada coincide no escribe absolutamente nada en la salida estándar.

## Entender los resultados

### Lectura incremental

El plugin mantiene un índice por fichero de log y tipo de origen en `--idx-dir`. El índice guarda la posición en bytes donde se dejó de leer.

Cuando el plugin encuentra un fichero de log por primera vez, lo registra en su final actual y no captura nada, de modo que el contenido histórico nunca se vuelca. En ejecuciones posteriores lee desde la posición guardada y procesa solo las líneas nuevas.

Eliminar o perder un índice hace que ese fichero de log vuelva a empezar al final del fichero: la siguiente ejecución lo registra en su final actual y omite las líneas ya escritas.

El análisis no es recursivo. Solo se consideran los ficheros que están directamente dentro de `--dir`, y los subdirectorios se ignoran.

### Rotación y truncado

El plugin detecta cuándo un fichero de log ha sido reemplazado o truncado:

- Si el fichero se renombró y se creó uno nuevo con el mismo nombre, el plugin detecta el nuevo fichero y lo lee desde el principio.
- Si el fichero es más pequeño que la posición guardada, el plugin reinicia la lectura desde el principio.

### Mantenimiento de los índices

En cada ejecución el plugin elimina los índices cuyo fichero de log ya no existe, lo que evita que el directorio de índices crezca con entradas de logs borrados. Nunca modifica ficheros de índice que no son suyos.

### Modelo de coincidencia

- La coincidencia se aplica a cada línea física del log.
- La coincidencia distingue mayúsculas de minúsculas. Un patrón que deba ignorarlas necesita un `(?i)` explícito, como en `(?i)error`.
- Una entrada de varias líneas, como una traza de pila, se captura como fragmentos de línea separados y no puede coincidir como un todo.
- El texto se trata como UTF-8. UTF-16 y las páginas de códigos de la plataforma no se decodifican, por lo que un patrón UTF-8 no coincide con un fichero de log escrito en otra codificación.
- Un BOM UTF-8 al principio de un fichero de log se elimina antes de la coincidencia, de modo que los anclajes `^` siguen aplicándose a la primera línea.

### Salida

Por cada fichero analizado que tenga líneas nuevas coincidentes, el plugin emite una entrada `log_module`:

| Campo | Contenido |
| --- | --- |
| `source` | El valor de `--source-type`, tal cual. Identifica el origen de los datos en Pandora FMS. |
| `data` | Las líneas coincidentes unidas por saltos de línea y codificadas en Base64, entre comillas dobles. El serializador XML escribe cada comilla como `&#34;`. |
| `encoding` | Siempre `base64`. |

El plugin no crea módulos numéricos ni de estado: los módulos de log son su única salida.

## Operación y resolución de problemas

### Ejecución manual

El plugin recibe todas las opciones por línea de comandos:

```
pandora_logparser --dir <ruta> [opciones]
pandora_logparser --config <ruta> [opciones]
```

Capturar todas las líneas nuevas de ficheros `.log`:

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --idx-dir /var/tmp/pandora-logparser
```

Filtrar solo las líneas que coinciden con un patrón:

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
```

Filtrar por nombre de fichero y contenido con un directorio de índices propio:

```bash
pandora_logparser --dir /opt/app/logs --name-regex 'access.*\.log' --content-regex '^50[023]' --source-type http_errors --idx-dir /var/tmp/pandora-logparser
```

Leer todas las opciones de un fichero de configuración:

```bash
pandora_logparser --config /etc/pandora/logparser.conf
```

### Diagnóstico y código de salida

El plugin no tiene ninguna opción de verbose o depuración. La salida estándar contiene únicamente el XML generado y todos los diagnósticos van a la salida de error estándar, de modo que redirigir ambos flujos por separado mantiene los datos limpios.

Se emiten avisos cuando un índice no se puede resolver o crear, cuando un índice no se puede cargar, cuando falla la limpieza de índices huérfanos y cuando se omite una línea por superar `--max-line-bytes`. Se emiten errores cuando no se puede leer un directorio o un fichero de log, cuando no se puede construir un módulo de log y cuando no se puede guardar un índice.

El código de salida es `0` en una ejecución correcta o con `--help`, y `1` si la entrada no es válida o se produce un error de procesamiento.

### Limitaciones

- Una línea más larga que `--max-line-bytes` se omite con un aviso y el fichero sigue procesándose. El valor por defecto es `1048576` bytes.
- Un fichero que no termina en salto de línea mantiene su última línea parcial sin leer hasta que llega el terminador. Una línea que nunca se termina nunca se emite.
- El plugin valida como máximo los 64 KiB inmediatamente anteriores a la posición guardada. Una reescritura en el sitio que deje sin cambios la identidad del fichero, el tamaño y esos bytes no se detecta.
- Solo se decodifica UTF-8.
- El plugin no es recursivo e ignora los subdirectorios.

### Resolución de problemas

| Síntoma | Causa probable | Comprobación |
| --- | --- | --- |
| La primera ejecución no genera salida | Comportamiento esperado: el índice registra cada fichero en su final. | Añada una línea coincidente y ejecute el plugin de nuevo. |
| Un módulo nunca genera datos | Otro módulo usa el mismo `--source-type` sobre el mismo fichero, o se cambió el tipo de origen y el índice volvió a empezar al final del fichero. | Asigne a cada módulo su propio `--source-type`; consulte [Índices y el tipo de origen](#indices-y-el-tipo-de-origen). |
| Un patrón que funcionaba en otro sitio no coincide | La coincidencia distingue mayúsculas de minúsculas, o el fichero de log no está en UTF-8. | Añada `(?i)` si debe ignorar las mayúsculas; confirme la codificación del fichero. |
| Un patrón no ASCII no coincide en Windows | El agente convirtió la línea de comandos a la página de códigos ANSI antes de que el plugin arrancara. | Coloque el valor en el fichero de configuración o use `--content-regex-base64`; consulte [Windows: valores no ASCII y metacaracteres del shell](#windows-valores-no-ascii-y-metacaracteres-del-shell). |
| Un módulo cuyo patrón tiene una alternancia no se ejecuta nunca en Windows | `cmd.exe` parte el comando en la barra vertical sin proteger. | Mueva el patrón al fichero de configuración o páselo en Base64. |
| Falta una línea en la salida | La línea supera `--max-line-bytes`, o seguía sin terminador cuando se ejecutó el plugin. | Revise el aviso de la salida de error; aumente `--max-line-bytes` si es necesario. |
| `error: --dir is required unless the config file provides dir` | Ni la línea de comandos ni el fichero de configuración proporcionan un directorio. | Pase `--dir`, o añada `dir` al fichero de configuración. |
| Un patrón muy largo se rechaza o se trunca en Windows | La línea de comandos de Windows tiene un límite de longitud y Base64 aumenta el tamaño del patrón. | Coloque el patrón en el fichero de configuración. |

## Referencia

### Opciones de línea de comandos

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `--dir <ruta>` | Sí, salvo que el fichero de configuración proporcione `dir` | — | Directorio que se recorre en busca de ficheros de log. El análisis no es recursivo. |
| `--config <ruta>` | No | — | Lee los parámetros de un fichero de configuración UTF-8. |
| `--name-regex <regex>` | No | `.*` | Expresión regular para filtrar nombres de fichero. |
| `--content-regex <regex>` | No | `.*` | Expresión regular para filtrar líneas del log. Es incompatible con `--content-regex-base64`. |
| `--content-regex-base64 <valor>` | No | — | Valor Base64 que decodifica a la expresión regular de contenido. Es incompatible con `--content-regex`. |
| `--source-type <nombre>` | No | `syslog` | Valor del campo `source` de los módulos de log generados y parte de la identidad del índice. Un valor vacío recae en `syslog`. |
| `--idx-dir <ruta>` | No | Directorio temporal del sistema operativo | Directorio donde se almacenan los ficheros de índice. Se crea si no existe. |
| `--max-line-bytes <n>` | No | `1048576` | Tamaño máximo aceptado de una línea de log, en bytes. Debe ser un entero positivo. |
| `-h`, `--help` | No | — | Muestra la ayuda y termina con estado `0`. |

### Claves del fichero de configuración

| Clave | Valor por defecto | Descripción |
| --- | --- | --- |
| `dir` | — | Directorio que se recorre. Equivale a `--dir`. |
| `name_regex` | `.*` | Equivale a `--name-regex`. |
| `content_regex` | `.*` | Equivale a `--content-regex`. |
| `content_regex_base64` | — | Equivale a `--content-regex-base64`. |
| `source_type` | `syslog` | Equivale a `--source-type`. |
| `idx_dir` | Directorio temporal del sistema operativo | Equivale a `--idx-dir`. |
| `max_line_bytes` | `1048576` | Equivale a `--max-line-bytes`. Debe ser un entero válido. |

`content_regex` y `content_regex_base64` no pueden aparecer juntas en el mismo fichero.

### Sintaxis de las expresiones regulares

Los patrones admiten las construcciones habituales de expresiones regulares, como `(?i)` para ignorar mayúsculas y minúsculas, clases POSIX como `[[:digit:]]`, escapes hexadecimales como `\x20` y escapes Unicode como `\x{041E}`. No se admiten aserciones de contexto (lookaround): un patrón como `a(?=b)` se rechaza.

Ejemplos para el filtro por nombre de fichero:

```
.+\.log              → solo ficheros con extensión .log
access.*\.log        → ficheros que empiezan por "access" y terminan en ".log"
(app|sys)\.log       → ficheros "app.log" o "sys.log"
```

Ejemplos para el filtro por contenido:

```
(?i)error                → líneas que contienen "error", sin distinguir mayúsculas
(?i)error|critical|fail  → líneas con error, critical o fail
^ERROR                   → líneas que empiezan por ERROR
[0-9]{3}\s               → líneas con un código de tres dígitos seguido de un espacio
```

`--content-regex-base64` acepta los alfabetos Base64 estándar y URL-safe, con o sin relleno, y debe decodificar a UTF-8 válido; se ignoran un BOM inicial y los bytes CR/LF finales. Para pasar valores no ASCII a través del agente de Windows, consulte [Windows: valores no ASCII y metacaracteres del shell](#windows-valores-no-ascii-y-metacaracteres-del-shell).
