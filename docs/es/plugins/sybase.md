# Plugin de monitorización de Sybase

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización de Sybase monitoriza un servidor Sybase ASE (Adaptive Server Enterprise) desde Pandora FMS. En cada ejecución recoge dos tipos de datos y los convierte en módulos de Pandora FMS:

- **Estado del servidor, leído con SQL.** Mediante la utilidad `isql` de Sybase, el plugin lee los catálogos del Adaptive Server: bases de datos con su espacio asignado y utilizado, uso del log de transacciones y de los segmentos, conexiones de usuario, locks, procesos bloqueados, engines fuera de línea, bases de datos sospechosas e índices sospechosos.
- **Estado de los procesos locales.** A partir de la lista de procesos del host, el plugin informa de si los procesos del Adaptive Server y del servidor de copias están en ejecución, y de la memoria y la CPU que consumen.

El plugin se ejecuta como plugin de agente de Pandora FMS: cada ejecución imprime en la salida estándar un bloque XML `<module>` por cada módulo generado, y el agente de Pandora FMS instalado en ese host los incorpora al agente del endpoint. El plugin no crea ningún agente ni entrega datos por sí mismo, por lo que no es un plugin de servidor.

Como los módulos de proceso leen la lista de procesos local, ejecute el plugin en el host donde se ejecuta el servidor ASE. Ejecutado contra un servidor remoto, informa de los procesos de la máquina en la que se ejecuta.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.sybase`, versión `1.0` | Objetivo documentado | Entrada del Marketplace; consulte [Identidad del addon](#identidad-del-addon) |
| Windows 10 | `Compatible conocido` | La edición anterior de esta guía registra Windows 10 como sistema probado, y el paquete del Marketplace es un ejecutable de Windows. Sin revalidar para la versión `1.0` |
| Sistemas operativos distintos de Windows | `Sin validar` | No hay registro de pruebas; la entrada del Marketplace distribuye un único ejecutable de Windows |
| Versiones y ediciones de Sybase ASE | `Sin validar` | No se ha registrado una matriz de versiones para este addon |
| Versiones de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones. El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |
| Un script de entorno de Sybase existente en el host | `Requerido` | El plugin termina con código de salida `1` cuando `sybase_env_script` no apunta a un fichero existente |
| La utilidad `isql` de Sybase accesible desde el host | `Requerido` | Todas las comprobaciones SQL se ejecutan mediante `isql` |
| Un agente de Pandora FMS en el host de ASE | `Requerido` | El plugin se ejecuta como plugin de agente |

El addon se publica en el Marketplace de Pandora FMS, con descarga gratuita:

[https://marketplace.pandorafms.com/entries/pandorafms.sybase](https://marketplace.pandorafms.com/entries/pandorafms.sybase)

### Requisitos

1. **Un servidor Sybase ASE** accesible desde el host que ejecuta el plugin, con el nombre de servidor y el puerto que configure.
2. **La utilidad `isql` de Sybase y el script de entorno de Sybase** en ese host. `isql` se resuelve desde `PATH` de forma predeterminada y, en sistemas tipo Unix, el script de entorno se carga antes de cada consulta.
3. **Un usuario de Sybase** que pueda leer los catálogos y ejecutar los procedimientos de las comprobaciones que active; consulte [Credenciales de Sybase](#credenciales-de-sybase).
4. **Un agente de Pandora FMS en el mismo host**, que ejecuta el plugin e incorpora sus módulos.
5. **En Windows, las utilidades de línea de comandos que invoca el plugin**: `grep`, `wc`, `tail`, `head`, `sed` y `gawk` en `PATH`, junto con `tasklist` y `typeperf` de Windows.

### Credenciales de Sybase

Cada comprobación lee tablas del sistema de ASE o ejecuta un procedimiento almacenado de ASE. El usuario necesita acceso a los objetos de las comprobaciones que active:

| Comprobación | Lee |
| --- | --- |
| `Sybase Databases in <server>` | `sp_helpdb` |
| `Sybase Max Size Available`, `Sybase Used Size global`, `Used size<database>` | `master..sysdatabases`, `master..sysusages`, `curunreservedpgs`, `@@maxpagesize` |
| `Sybase Connections Used Ratio`, `Sybase Connections Remaining` | `master..sysprocesses`, `master..syslogins`, `sp_configure 'number of user connections'` |
| `Sybase Num Blocked Processes` | `sp_who` |
| `Sybase Blocker Processes` | `master..sysprocesses` |
| `Sybase Engines Offline` | `master..sysengines` |
| `Sybase Suspect Databases` | `master..sysdatabases` |
| `Sybase Mirror Devices` | `master..sysdevices` |
| `Sybase Locks Remaining` | `sysconfigures`, `syslocks` |
| `Sybase Suspect Index` | `sysindexes` |
| `Log Space Used <database>` | `sp_helpsegment logsegment` |
| `Sybase Segment space [<segment>][<database>]` | `sp_helpsegment` |

Ninguna fuente oficial define una lista de permisos más restrictiva que estas lecturas; conceda solo lo que necesiten las comprobaciones que active y utilice un usuario dedicado para Pandora FMS.

La contraseña se guarda en el archivo de configuración en texto plano y se pasa a `isql` en su línea de comandos, por lo que es visible en la lista de procesos del host mientras se ejecuta una consulta. Restrinja el archivo de configuración a la cuenta que ejecuta el agente y utilice un usuario de Sybase dedicado.

### Instalar el addon

Descargue el addon desde su entrada del Marketplace. La entrada distribuye el ejecutable `pandorafms.sybase.1.0.exe`: cópielo en el directorio de plugins del agente de Pandora FMS del host de ASE, por ejemplo `C:\Program Files\Pandora_Agent\plugins\`, y cree junto a él el archivo de configuración `pandora_sybase.conf`. El archivo completo se documenta en [Configuración de ejemplo](#configuracion-de-ejemplo).

## Configuración

### Archivo de configuración

El plugin recibe su archivo de configuración como único argumento posicional:

```bat
pandorafms.sybase.1.0.exe <PATH_TO_CONFIG>
```

El archivo es texto plano con una línea `clave = valor` por línea. Se omiten las líneas en blanco y las que empiezan por `#`, se recortan las claves y los valores y, si una clave se repite, prevalece el último valor.

Cualquier clave escalar se puede sobrescribir en la línea de comandos sin editar el archivo, con pares `-clave valor` después de la ruta del archivo:

```bat
pandorafms.sybase.1.0.exe <PATH_TO_CONFIG> -debug 1 -username <USERNAME>
```

Las listas de objetivos y los umbrales se leen solo del archivo: pasarlos como opciones no tiene efecto (consulte [Ejecución por línea de comandos](#ejecucion-por-linea-de-comandos)).

### Ajustes de conexión

Estas claves identifican el entorno de cliente y el inicio de sesión principal:

```ini
GLOBAL_SERVERNAME = <ASE_SERVER_NAME>
sybase_env_script = /opt/sybase/SYBASE.sh
isql = isql
encryption = 0

username = <USERNAME>
password = <PASSWORD>
servername = <ASE_SERVER_NAME>
port = 5000
```

- `GLOBAL_SERVERNAME` identifica el Adaptive Server local. Debe aparecer en la línea de comandos del proceso `dataserver` local, porque los dos módulos de estado buscan ese proceso por este valor.
- `sybase_env_script` es el script de entorno de Sybase. El plugin exige que el fichero exista en cualquier plataforma y se detiene con `Error, cannot found sybase environment script at [...]` y código de salida `1` cuando no existe. En sistemas tipo Unix se carga antes de cada llamada a `isql`, por lo que debe poder cargarse en un shell no interactivo. En Windows no se carga, y el entorno de Sybase debe estar ya presente en el entorno del agente de Pandora FMS.
- `isql` es el comando o la ruta completa de la utilidad `isql` de Sybase. El valor predeterminado, `isql`, la resuelve desde `PATH`.
- `encryption = 1` añade la opción `-X` a la invocación de `isql`, que solicita una conexión cifrada. Requiere que el cliente de Sybase esté configurado para ello.
- `username` y `password` son el usuario que utilizan todas las comprobaciones que no definen credenciales propias.
- `servername` y `port` se pasan a `isql` como `-S <servername>:<port>`. Cuando la clave `port` no está presente, se pasa solo el nombre de servidor.

### Comprobaciones por base de datos y de inicio de sesión

Tres listas numeradas añaden comprobaciones a los módulos del servidor. Cada entrada tiene un sufijo numérico y su propio formato:

| Lista | Formato | Módulo generado |
| --- | --- | --- |
| `check_dbsizeNN` | `<database>` | Porcentaje utilizado, espacio del log, disponibilidad y un módulo de segmento por cada segmento de esa base de datos |
| `check_instanceNN` | `<user>;<password>;<database>` | `Sybase Instance '<database>' availability` |
| `custom_checkNN` | `<user>;<password>;<database>` | `Sybase Login check <database>` |

```ini
check_dbsize01 = <DB_NAME>
check_instance01 = <USERNAME>;<PASSWORD>;<DB_NAME>
custom_check01 = <USERNAME>;<PASSWORD>;<DB_NAME>
```

- El sufijo solo distingue las entradas; el archivo de referencia las numera desde `01`. No hay clave de recuento total: se lee toda entrada presente en el archivo.
- Dos entradas que nombran la misma base de datos generan un único conjunto de módulos.
- El tercer campo de `check_instanceNN` y `custom_checkNN` es un nombre de **base de datos**, no un nombre de servidor ASE: el plugin inicia sesión en esa base de datos para probar las credenciales. El archivo de configuración de referencia etiqueta ese campo como instancia.
- Las entradas `check_dbsizeNN` usan `username` y `password` principales, nunca credenciales propias.
- Los módulos por base de datos de `check_dbsizeNN` y los módulos de `check_instanceNN` solo se generan cuando el inicio de sesión principal tiene éxito (consulte [Entender los resultados](#entender-los-resultados)). Los módulos de `custom_checkNN` se generan aunque falle.

### Activar los módulos necesarios

Cada módulo del servidor y cada módulo local tiene su propio interruptor. El valor `1` activa el módulo; `0`, un valor vacío o una clave ausente lo desactivan. Todos los interruptores están desactivados de forma predeterminada, por lo que el archivo de configuración declara explícitamente qué módulos desea:

```ini
sybase_main_status = 1
sybase_backup_status = 1
sybase_memuse = 1
sybase_cpuusage = 1
sybase_count_databases = 1
sybase_max_size = 1
sybase_used_size = 1
sybase_connections_used_ratio = 1
sybase_available_connections = 1
sybase_blocked_processes = 1
sybase_offline_engines = 1
sybase_suspects_databases = 1
```

La lista completa, con el módulo que activa cada interruptor, está en [Interruptores de módulos](#interruptores-de-modulos).

### Registrar el plugin en el agente

El agente de Pandora FMS ejecuta los plugins de agente declarados en su archivo de configuración, `pandora_agent.conf`. Añada una línea `module_plugin` con el ejecutable y el archivo de configuración:

```ini
module_plugin "C:\Program Files\Pandora_Agent\plugins\pandorafms.sybase.1.0.exe" "C:\Program Files\Pandora_Agent\plugins\pandora_sybase.conf"
```

Reinicie el agente después del cambio. El agente ejecuta el plugin en cada intervalo del agente e incorpora los módulos que imprime, por lo que el intervalo de los módulos es el del agente que los contiene. Cuando la configuración del agente se gestiona desde la consola, añada la misma línea desde la consola en lugar de editar el archivo en el host.

Solo un agente debe ejecutar el plugin para un mismo servidor ASE: dos agentes que lo ejecuten contra el mismo servidor crean dos conjuntos de módulos distintos.

### Credenciales y transporte

- El archivo de configuración contiene en texto plano la contraseña principal y la de cada entrada `check_instanceNN` y `custom_checkNN`. Restrinja sus permisos a la cuenta que ejecuta el agente.
- Todas las consultas pasan la contraseña a `isql` como argumento de línea de comandos, por lo que la contraseña es visible en la lista de procesos del host mientras se ejecuta una consulta. Mantenga las credenciales en el archivo de configuración: una opción `-username` o `-password` escrita en la línea de comandos permanece además en el historial del shell del host.
- `encryption = 1` añade `-X` a todas las llamadas a `isql`, lo que solicita al cliente de Sybase una conexión cifrada. Confirme que el cliente y el servidor están configurados para ello antes de activar la opción; de lo contrario, las comprobaciones de inicio de sesión fallan.

## Verificación

Ejecute el plugin manualmente, pasando el archivo de configuración como único argumento posicional:

```bat
pandorafms.sybase.1.0.exe <PATH_TO_CONFIG>
```

Una ejecución correcta imprime en la salida estándar un bloque XML `<module>` por cada módulo generado y termina con código de salida `0`. El extracto siguiente muestra cuatro de ellos; los valores son ilustrativos:

```xml
<module>
	<name><![CDATA[Sybase ASE status]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[The status of the Adaptive Server]]></description>
</module>
<module>
	<name><![CDATA[Sybase Memory Use]]></name>
	<type>generic_data</type>
	<data><![CDATA[120.63]]></data>
	<description><![CDATA[Sybase memory use in MB]]></description>
	<unit><![CDATA[MB]]></unit>
</module>
<module>
	<name><![CDATA[Sybase Database <DB_NAME> availability]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Availability for <DB_NAME>]]></description>
</module>
<module>
	<name><![CDATA[Log Space Used <DB_NAME>]]></name>
	<type>generic_data</type>
	<data><![CDATA[18.40]]></data>
	<unit><![CDATA[%]]></unit>
</module>
```

- `pandorafms.sybase.1.0.exe -h` imprime el resumen de uso y termina con código de salida `0`. El resumen se escribe en el error estándar, no en la salida estándar, y `-h` solo se reconoce como primer argumento.
- Una ejecución que no encuentra el script de entorno imprime `Error, cannot found sybase environment script at [...]` en el error estándar, seguido del resumen de uso, y termina con código de salida `1`.
- Una ejecución cuyas consultas fallan termina igualmente con código de salida `0`: los módulos que fallan simplemente no aparecen en la salida. Use `debug = 1` para ver el motivo (consulte [Operación y solución de problemas](#operacion-y-solucion-de-problemas)).

Una vez reiniciado el agente, los módulos aparecen en la consola bajo el agente del endpoint:

<!-- SCREENSHOT NEEDED: Agent module list in the Pandora FMS console after a successful Sybase plugin run, showing the local and server-wide modules. -->

## Entender los resultados

Los módulos se agrupan en cuatro bloques:

- **Host local.** `Sybase ASE status` y `Sybase ASE Backup server status` informan de `1` mientras los procesos locales `dataserver` y `backupserver` están en ejecución, y de `0` en caso contrario. Son comprobaciones de proceso, no de conectividad: no indican si `isql` puede alcanzar el servidor. `Sybase Memory Use` y `Sybase CPU Busy` describen el proceso local del Adaptive Server.
- **Servidor.** `Sybase Databases in <server>`, `Sybase Max Size Available`, `Sybase Used Size global`, `Sybase Connections Used Ratio`, `Sybase Connections Remaining`, `Sybase Num Blocked Processes`, `Sybase Blocker Processes`, `Sybase Engines Offline`, `Sybase Suspect Databases`, `Sybase Mirror Devices`, `Sybase Locks Remaining`, `Sybase Suspect Index` y `Used size all databases` se leen con SQL del servidor configurado.
- **Por base de datos.** Cada entrada `check_dbsizeNN` añade `Used size<database>`, `Log Space Used <database>`, `Sybase Database <database> availability` y un módulo `Sybase Segment space [<segment>][<database>]` por cada segmento de la base de datos.
- **Comprobaciones de inicio de sesión.** Cada entrada `check_instanceNN` añade un módulo de disponibilidad y cada entrada `custom_checkNN` añade un módulo de comprobación de inicio de sesión; ambos informan de `1` cuando el inicio de sesión funciona y de `0` cuando no.

**El inicio de sesión principal condiciona los módulos SQL.** Antes de las comprobaciones del servidor, el plugin inicia sesión con `username` y `password`. Cuando ese inicio de sesión falla, los módulos del servidor y los módulos de `check_dbsizeNN` y `check_instanceNN` no se generan en absoluto y ningún módulo informa del fallo; solo aparecen los módulos locales y las comprobaciones `custom_checkNN`. Use `debug = 1` para ver el error de `isql`.

**Umbrales.** Los módulos numéricos llevan los umbrales de aviso y crítico definidos en el archivo de configuración bajo `thresholds.<clave>.<wmin|wmax|cmin|cmax>`; Pandora FMS los evalúa como los de cualquier otro módulo. Consulte [Umbrales](#umbrales) para las claves y los valores de referencia.

**Orden.** Los módulos generados desde `check_dbsizeNN`, `check_instanceNN` y `custom_checkNN` no se emiten en el orden del archivo de configuración y su orden varía entre ejecuciones.

## Operación y solución de problemas

El plugin no guarda estado entre ejecuciones: cada ejecución consulta el servidor y la lista de procesos local en ese momento, por lo que se puede ejecutar manualmente en cualquier momento sin afectar a la siguiente ejecución programada.

Ajuste `debug = 1` para publicar diagnósticos en el error estándar. Cada mensaje lleva la fecha y la hora, y el canal informa del texto de error de `isql` y de los fallos de análisis de segmentos; sin él, el plugin no informa de las consultas fallidas.

### Limitaciones conocidas

Estos comportamientos corresponden a la versión actual:

- **Módulos de log de errores.** `sybase_errorlog_size`, `sybase_errorlog` y `sybase_errorlog_updates` existen como interruptores, pero ninguna clave de configuración establece el directorio de logs de Sybase en esta versión. El módulo de tamaño informa de `0.00`, el módulo de ruta informa de un valor vacío y el contador de actualizaciones no recibe ningún directorio, así que deje los tres interruptores desactivados.
- **`sybase_logsize`.** El archivo de configuración de referencia establece esta clave, pero ninguna comprobación la lee.
- **Nombre del porcentaje por base de datos.** El módulo concatena el prefijo y el nombre de la base de datos sin un espacio de separación: una base de datos llamada `master` genera `Used sizemaster`.
- **Porcentajes por base de datos.** `sybase_used_size_percent` activa solo `Used size all databases`; los porcentajes por base de datos los crean las entradas `check_dbsizeNN`.
- **Unidad de memoria.** `Sybase Memory Use` publica el valor con unidad `MB`; en sistemas tipo Unix el valor es la suma de la columna `%MEM` de la lista de procesos.
- **Sin módulo de fallo.** Un inicio de sesión principal fallido no deja ningún módulo; diagnostíquelo con `debug = 1`.

### Fallos habituales

- **`Error, cannot found sybase environment script at [...]` y código de salida `1`** — `sybase_env_script` está vacío o no apunta a un fichero existente. Indique el script de entorno de Sybase del host, por ejemplo `C:\SAP\...\SYBASE.bat` en Windows o `/opt/sybase/SYBASE.sh` en sistemas tipo Unix. El plugin exige el fichero incluso en Windows, donde no lo carga.
- **El plugin imprime el resumen de uso y ningún XML de módulos** — se pasó `-h` como primer argumento, o la ruta del archivo de configuración no existe. Una ruta inexistente no se informa como fichero ausente: se lee como una opción de configuración y la ejecución termina con el error del script de entorno.
- **No aparece ningún módulo del servidor, pero sí los módulos locales** — el inicio de sesión principal falló, así que se omitieron todos los módulos SQL. Ejecute con `debug = 1` y revise el error de `isql`: `username` o `password` incorrectos, un `servername` o `port` que no se resuelve, o un usuario sin acceso a los catálogos.
- **`Sybase ASE status` vale `0` con el servidor en ejecución** — `GLOBAL_SERVERNAME` no aparece en la línea de comandos del proceso `dataserver` local. Ajuste el valor al nombre que informa el proceso.
- **`Sybase Memory Use` y `Sybase CPU Busy` informan de `0`** — el plugin no se ejecuta en el host del servidor ASE, o la cuenta local no puede ver el proceso del servidor en la lista de procesos.
- **Una base de datos de `check_dbsizeNN` no tiene módulos** — el inicio de sesión principal falló, o el nombre de la base de datos de la entrada no existe. Una base de datos inexistente genera el módulo de disponibilidad con valor `0`; los módulos de segmento se omiten y, con `debug = 1`, se informa del error de análisis de segmentos.
- **Faltan módulos `Sybase Segment space [...]` para una base de datos** — las bases de datos del sistema `sybsystemprocs`, `sybsystemdb`, `model` y `tempdb` se omiten por diseño, y una base de datos cuyos segmentos no se pueden leer no genera módulo de segmento.
- **`Used size<database>` o `Log Space Used <database>` informa de `0`** — el usuario no puede leer `master..sysusages` ni ejecutar `sp_helpsegment`, o la base de datos no existe.
- **Los módulos de log de errores informan de `0.00`, de una ruta vacía o de nada** — esta versión no lee el directorio de logs de Sybase desde la configuración, por lo que `sybase_errorlog_size`, `sybase_errorlog` y `sybase_errorlog_updates` no pueden producir un valor. Déjelos desactivados; consulte [Limitaciones conocidas](#limitaciones-conocidas).
- **Los módulos no aparecen en la consola** — compruebe que la línea `module_plugin` apunta al ejecutable y al archivo de configuración, que el agente se reinició y que el agente puede ejecutar el fichero. El log del agente registra el resultado de la ejecución.

## Referencia

### Archivo de configuración

El archivo usa líneas `clave = valor`. Se omiten las líneas en blanco y las que empiezan por `#`, se recortan las claves y los valores y prevalece la última aparición de una clave repetida. Los números se leen como texto, así que escriba `1` para activar un interruptor y `0` para desactivarlo.

| Nombre | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `GLOBAL_SERVERNAME` | Sí | — | Nombre del Adaptive Server local. Debe aparecer en la línea de comandos del proceso `dataserver` local y se usa en el nombre del módulo de log de errores. |
| `sybase_env_script` | Sí | Vacío | Script de entorno de Sybase. Se carga antes de cada llamada a `isql` en sistemas tipo Unix; el fichero debe existir en cualquier plataforma. |
| `isql` | No | `isql` | Comando o ruta completa de la utilidad `isql` de Sybase. |
| `encryption` | No | `0` | `1` añade la opción `-X` a todas las llamadas a `isql`. |
| `username` | Sí | — | Usuario de las comprobaciones principales y de `check_dbsizeNN`. |
| `password` | Sí | — | Contraseña de `username`. |
| `servername` | Sí | — | Nombre del servidor ASE, que se pasa a `isql` con `-S`. |
| `port` | No | Ausente (sin puerto) | Puerto que se pasa a `isql` como `<servername>:<port>`. Cuando la clave no está presente, se pasa solo el nombre de servidor. |
| `debug` | No | `0` | `1` imprime diagnósticos con fecha y hora en el error estándar. |
| `check_dbsizeNN` | No | — | `<database>`. Añade los módulos de porcentaje utilizado, espacio del log, disponibilidad y segmentos de esa base de datos. |
| `check_instanceNN` | No | — | `<user>;<password>;<database>`. Añade `Sybase Instance '<database>' availability`. |
| `custom_checkNN` | No | — | `<user>;<password>;<database>`. Añade `Sybase Login check <database>`. |
| `grep_log` | No | Vacío | Ruta del auxiliar `grep_log` que usa la comprobación de actualizaciones del log de errores. Esa comprobación no puede producir un valor en esta versión. |
| `custom_error_terms` | No | Lista de términos integrada | Expresión regular de los términos que cuenta la comprobación de actualizaciones del log de errores. |

### Interruptores de módulos

| Clave | Módulo que activa |
| --- | --- |
| `sybase_main_status` | `Sybase ASE status` |
| `sybase_backup_status` | `Sybase ASE Backup server status` |
| `sybase_memuse` | `Sybase Memory Use` |
| `sybase_cpuusage` | `Sybase CPU Busy` |
| `sybase_count_databases` | `Sybase Databases in <server>` |
| `sybase_max_size` | `Sybase Max Size Available` |
| `sybase_used_size` | `Sybase Used Size global` |
| `sybase_used_size_percent` | `Used size all databases`; los porcentajes por base de datos provienen de `check_dbsizeNN` |
| `sybase_connections_used_ratio` | `Sybase Connections Used Ratio` |
| `sybase_available_connections` | `Sybase Connections Remaining` |
| `sybase_blocked_processes` | `Sybase Num Blocked Processes` |
| `sybase_blocker_processes` | `Sybase Blocker Processes` |
| `sybase_offline_engines` | `Sybase Engines Offline` |
| `sybase_suspects_databases` | `Sybase Suspect Databases` |
| `sybase_mirror_devices` | `Sybase Mirror Devices` |
| `sybase_locks_remaining` | `Sybase Locks Remaining` |
| `sybase_suspect_index` | `Sybase Suspect Index` |
| `sybase_errorlog_size` | `Error Log Size`; no puede producir un valor en esta versión |
| `sybase_errorlog` | `Sybase ErrorLog path`; no puede producir un valor en esta versión |
| `sybase_errorlog_updates` | Contador de actualizaciones del log de errores; no puede producir un valor en esta versión |

El archivo de configuración de referencia activa doce de estos interruptores y además establece `sybase_logsize`, una clave que ninguna comprobación lee. Para activar el módulo de tamaño del log de errores, use `sybase_errorlog_size`.

### Umbrales

Cada módulo numérico publica los umbrales definidos para su clave. Una clave con valor vacío deja el umbral sin definir; `0` es un valor real. Estos son los valores del archivo de configuración de referencia:

| Clave | Módulo | `wmin` | `wmax` | `cmin` | `cmax` |
| --- | --- | --- | --- | --- | --- |
| `sybase_used_size` | `Used size<database>` | `90` | `95` | `95` | `100` |
| `sybase_used_size_all` | `Used size all databases` | `85` | `90` | `90` | `100` |
| `sybase_memuse` | `Sybase Memory Use` | — | — | — | — |
| `sybase_cpuusage` | `Sybase CPU Busy` | — | — | `90` | `100` |
| `sybase_connections_used_ratio` | `Sybase Connections Used Ratio` | `85` | — | `90` | — |
| `sybase_available_connections` | `Sybase Connections Remaining` | `5` | `15` | `0` | `5` |
| `sybase_blocked_processes` | `Sybase Num Blocked Processes` | `0` | `0` | `1` | `0` |
| `sybase_blocker_processes` | `Sybase Blocker Processes` | `0` | `0` | `1` | `0` |
| `sybase_offline_engines` | `Sybase Engines Offline` | `0` | `0` | `1` | `0` |
| `sybase_suspects_databases` | `Sybase Suspect Databases` | `0` | `0` | `1` | `0` |
| `sybase_locks_remaining` | `Sybase Locks Remaining` | `50` | `100` | `0` | `50` |
| `sybase_segment_space` | `Sybase Segment space [...]` | `80` | `0` | `90` | `0` |
| `sybase_suspect_index` | `Sybase Suspect Index` | `0` | `0` | `1` | `0` |
| `sybase_errorlog_size` | `Error Log Size` | `100` | — | `250` | — |

Las claves de umbral no tienen efecto en módulos que no publican umbrales, como `Sybase Max Size Available` y `Sybase Used Size global`.

### Ejecución por línea de comandos

```bat
pandorafms.sybase.1.0.exe [archivo-configuración] [-clave valor ...]
```

| Condición | Comportamiento |
| --- | --- |
| El primer argumento es `-h` | Imprime el resumen de uso en el error estándar y termina con código de salida `0` |
| El primer argumento nombra un fichero existente | Se ejecuta con ese fichero y las opciones restantes |
| El primer argumento nombra un fichero inexistente | Trata la ruta como una opción de configuración y se detiene con el error del script de entorno; código de salida `1` |
| Ningún argumento | Imprime el error del script de entorno y el resumen de uso en el error estándar, y termina con código de salida `1` |
| `-clave valor` | Sobrescribe el valor de configuración de la misma clave |
| `-clave=valor` | No es una opción: el token completo se convierte en una clave de configuración y no tiene efecto |
| Un argumento final sin pareja | Se ignora |
| `check_dbsizeNN`, `check_instanceNN`, `custom_checkNN` o `thresholds.*` como opción | No tiene efecto; se leen solo del archivo de configuración |

El plugin mantiene el código de salida `0` cuando fallan consultas concretas, e informa del fallo solo mediante los módulos ausentes y los diagnósticos de `debug = 1`.

### Módulos generados

En los nombres siguientes, `<server>` es el valor de `servername`, `<database>` una base de datos de una entrada `check_dbsizeNN` y `<segment>` un segmento de esa base de datos:

| Nombre del módulo | Tipo | Activado por | Significado |
| --- | --- | --- | --- |
| `Sybase ASE status` | `generic_proc` | `sybase_main_status` | `1` mientras se ejecuta el proceso local `dataserver` que coincide con `GLOBAL_SERVERNAME`, `0` en caso contrario |
| `Sybase ASE Backup server status` | `generic_proc` | `sybase_backup_status` | `1` mientras se ejecuta el proceso local `backupserver` que coincide con `GLOBAL_SERVERNAME`, `0` en caso contrario. En Windows el proceso es `bcksrvr.exe` |
| `Sybase Memory Use` | `generic_data`, unidad `MB` | `sybase_memuse` | Memoria que usa el proceso local del Adaptive Server, según la lista de procesos |
| `Sybase CPU Busy` | `generic_data`, unidad `%` | `sybase_cpuusage` | CPU que usa el proceso local del Adaptive Server |
| `Sybase Databases in <server>` | `generic_data` | `sybase_count_databases` | Bases de datos que lista `sp_helpdb`, excluidas las marcadas como `dbo use only` |
| `Sybase Max Size Available` | `generic_data`, unidad `MB` | `sybase_max_size` | Espacio asignado a todas las bases de datos, excluidos los segmentos de log |
| `Sybase Used Size global` | `generic_data`, unidad `MB` | `sybase_used_size` | Espacio utilizado de todas las bases de datos, excluidos los segmentos de log |
| `Used size all databases` | `generic_data`, unidad `%` | `sybase_used_size_percent` | Porcentaje utilizado del espacio asignado a todas las bases de datos; `0` cuando no se puede leer el tamaño asignado |
| `Sybase Connections Used Ratio` | `generic_data`, unidad `%` | `sybase_connections_used_ratio` | Conexiones de usuario en uso frente al máximo configurado |
| `Sybase Connections Remaining` | `generic_data` | `sybase_available_connections` | Máximo configurado menos las conexiones en uso |
| `Sybase Num Blocked Processes` | `generic_data` | `sybase_blocked_processes` | Entradas de `sp_who` en estado `lock sleep` |
| `Sybase Blocker Processes` | `generic_data` | `sybase_blocker_processes` | Procesos que retienen locks y bloquean a otros procesos |
| `Sybase Engines Offline` | `generic_data` | `sybase_offline_engines` | Engines informados como fuera de línea en `master..sysengines` |
| `Sybase Suspect Databases` | `generic_data` | `sybase_suspects_databases` | Bases de datos con estado `256` o `320` |
| `Sybase Mirror Devices` | `generic_data` | `sybase_mirror_devices` | Dispositivos configurados para espejo que no se están replicando en ese momento |
| `Sybase Locks Remaining` | `generic_data` | `sybase_locks_remaining` | Locks configurados menos los locks de `syslocks` |
| `Sybase Suspect Index` | `generic_data` | `sybase_suspect_index` | Índices marcados como sospechosos |
| `Used size<database>` | `generic_data`, unidad `%` | `check_dbsizeNN` | Porcentaje utilizado del espacio asignado a la base de datos |
| `Log Space Used <database>` | `generic_data`, unidad `%` | `check_dbsizeNN` | Porcentaje utilizado del segmento de log de transacciones de la base de datos |
| `Sybase Database <database> availability` | `generic_proc` | `check_dbsizeNN` | `1` cuando `isql` inicia sesión en la base de datos, `0` en caso contrario |
| `Sybase Segment space [<segment>][<database>]` | `generic_data`, unidad `%` | `check_dbsizeNN` | Porcentaje utilizado de cada segmento de la base de datos |
| `Sybase Instance '<database>' availability` | `generic_proc` | `check_instanceNN` | `1` cuando las credenciales de la entrada inician sesión en la base de datos, `0` en caso contrario |
| `Sybase Login check <database>` | `generic_proc` | `custom_checkNN` | `1` cuando las credenciales de la entrada inician sesión en la base de datos, `0` en caso contrario |

### Configuración de ejemplo

```ini
# Identificación del servidor local
GLOBAL_SERVERNAME = <ASE_SERVER_NAME>

# Entorno de cliente de Sybase
sybase_env_script = /opt/sybase/SYBASE.sh
isql = isql
encryption = 0

# Inicio de sesión principal
username = <USERNAME>
password = <PASSWORD>
servername = <ASE_SERVER_NAME>
port = 5000

# Comprobaciones por base de datos
check_dbsize01 = <DB_NAME>

# Comprobaciones de inicio de sesión
custom_check01 = <USERNAME>;<PASSWORD>;<DB_NAME>

# Módulos
sybase_main_status = 1
sybase_backup_status = 1
sybase_memuse = 1
sybase_cpuusage = 1
sybase_count_databases = 1
sybase_max_size = 1
sybase_used_size = 1
sybase_connections_used_ratio = 1
sybase_available_connections = 1
sybase_blocked_processes = 1
sybase_offline_engines = 1
sybase_suspects_databases = 1

# Umbrales
thresholds.sybase_used_size.wmin = 90
thresholds.sybase_used_size.wmax = 95
thresholds.sybase_used_size.cmin = 95
thresholds.sybase_used_size.cmax = 100
thresholds.sybase_segment_space.wmin = 80
thresholds.sybase_segment_space.cmin = 90
```

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.sybase` |
| Nombre | Sybase |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2026-05-25 |
| Fichero distribuido | `pandorafms.sybase.1.0.exe` |
| Licencia | Descarga gratuita |
| Autor | Pandora FMS |
