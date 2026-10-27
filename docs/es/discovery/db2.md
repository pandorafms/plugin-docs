# DB2 Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de DB2 monitoriza bases de datos IBM Db2 de forma remota. Una tarea de Discovery se conecta a cada base de datos que indique y convierte el resultado en agentes y módulos de Pandora FMS: disponibilidad de la conexión, resumen de rendimiento de la base de datos, utilización del log de transacciones, tamaño de la base de datos, conexiones activas y estadísticas de caché de los buffer pools. También puede ejecutar sus propias consultas `SELECT` de solo lectura y publicar su resultado como módulos.

Una tarea de Discovery genera **un agente por cada base de datos objetivo**. No se instala nada en el servidor de base de datos: el addon se conecta por TCP/IP desde el servidor de Discovery con un usuario y una contraseña de base de datos.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.db2`, versión `1.2` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a cada listener de Db2 (TCP, puerto por defecto `50000`) | `Requerido` | El addon se conecta con el protocolo TCP/IP |
| Un usuario de Db2 con los permisos de [Usuario de base de datos](#usuario-de-base-de-datos) | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Versiones y plataformas del servidor Db2 | `Sin validar` | No se ha registrado una matriz de versiones de Db2 para este addon |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a cada listener de Db2 que quiera monitorizar.
2. **Un usuario y una contraseña de base de datos** con los permisos descritos a continuación. El mismo usuario y contraseña se usan para todos los objetivos de la tarea.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

No hace falta instalar ningún cliente IBM Db2 en el servidor de Discovery.

### Usuario de base de datos

Cada opción lee vistas administrativas de Db2, por lo que el usuario necesita acceso `SELECT` a las vistas de las opciones que active. Cuando se rechaza una consulta, el addon informa de un error que pide verificar los permisos (consulte [Solución de problemas](#solucion-de-problemas)).

| Opción | Vista de Db2 leída |
|--------|--------------------|
| Siempre | `SYSIBMADM.ENV_INST_INFO` (nivel de servicio de la instancia, mostrado como versión del sistema operativo del agente) |
| **Get database summary** | `SYSIBMADM.MON_DB_SUMMARY` |
| **Check transactional log utilization** | `SYSIBMADM.MON_TRANSACTION_LOG_UTILIZATION` |
| **Check DB size** | `SYSIBMADM.ADMINTABINFO` |
| **Get number of connections** | `SYSIBMADM.MON_CONNECTION_SUMMARY` |
| **Retrieve cache statistics** | `SYSIBMADM.BP_HITRATIO` |
| **Execute custom queries** | Los objetos que lean sus propias consultas |

Ninguna fuente oficial identifica un conjunto de privilegios más reducido que estas lecturas; conceda solo lo que necesiten las opciones que active.

La contraseña se escribe en el fichero de configuración temporal de la tarea en el servidor de Discovery mientras esta se ejecuta. Use un usuario dedicado para Pandora FMS.

### Instalar el addon

Descargue el paquete `.disco` de la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.db2](https://marketplace.pandorafms.com/entries/pandorafms.db2)

Cárguelo en Pandora FMS. Una vez cargado, **DB2** está disponible al crear tareas de Discovery de tipo aplicación.

<!-- SCREENSHOT NEEDED: Pantalla de creación de tareas de Discovery con la entrada de aplicación DB2 una vez cargado el paquete. -->

## Configurar la tarea de Discovery

Cree la tarea y elija **DB2**. La consola presenta los campos en dos pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **DB2 Base** — objetivos y credenciales:

    - **DB2 target strings**: las bases de datos a monitorizar, una `SERVER:PORT/DATABASE` por entrada, separadas por comas o una por línea. Las líneas que empiezan por `#` son comentarios. Consulte [Formato de los objetivos](#formato-de-los-objetivos).
    - **User** y **Password**: las credenciales de Db2. Ambas son obligatorias.

    <!-- SCREENSHOT NEEDED: Paso DB2 Base del asistente con un objetivo de laboratorio, un usuario y una contraseña enmascarada, sin nombres de host ni credenciales reales. -->

2. **DB2 Detailed** — ejecución y qué recopilar:

    - **Max threads**: cuántos objetivos se procesan en paralelo.
    - **Target agent**: nombres de los agentes generados.
    - **Custom module prefix**: texto que se antepone a todos los nombres de módulo.
    - **Get database summary**, **Check transactional log utilization**, **Get number of connections**, **Check DB size** y **Retrieve cache statistics**: activan cada grupo de módulos. Todos están activados por defecto.
    - **Execute custom queries** y **Custom queries**: ejecutan sus propias consultas. El cuadro de texto se muestra cuando **Execute custom queries** está activado. Consulte [Consultas personalizadas](#consultas-personalizadas).

    <!-- SCREENSHOT NEEDED: Paso DB2 Detailed del asistente con Max threads, Target agent, Custom module prefix y las casillas de recopilación. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

### Formato de los objetivos

Cada objetivo identifica un host, opcionalmente un puerto, y una base de datos:

| Forma | Host | Puerto | Base de datos |
|-------|------|--------|---------------|
| `<HOST>:<PORT>/<DATABASE>` | `<HOST>` | `<PORT>` | `<DATABASE>` |
| `<HOST>/<DATABASE>` | `<HOST>` | `50000` | `<DATABASE>` |

Para conectar es necesario el nombre de la base de datos. Un objetivo que no lo incluya (`<HOST>` o `<HOST>:<PORT>`) se acepta pero no puede conectar, por lo que su agente informa `DB2 connection` como `0`.

Ejemplo con dos objetivos:

```text
# Producción
<DB2_HOST_1>:50000/<DATABASE_1>, <DB2_HOST_2>/<DATABASE_2>
```

### Nombres de los agentes

Por defecto el agente se llama como su cadena de objetivo, por ejemplo `<HOST>:<PORT>/<DATABASE>`. Para elegir otros nombres, rellene **Target agent** con una lista separada por comas, un nombre por objetivo y en el mismo orden que los objetivos. Un objetivo sin nombre correspondiente conserva su cadena de objetivo como nombre de agente.

### Consultas personalizadas

Las consultas personalizadas permiten publicar el resultado de cualquier `SELECT` como módulo. Se aplican a todos los objetivos de la tarea. Cada consulta es un bloque de líneas entre `check_begin` y `check_end`; cada línea es una clave seguida de su valor. Las líneas que empiezan por `#` son comentarios.

```text
check_begin
name Blocked applications
description Applications waiting on a lock
operation value
datatype generic_data
target SELECT COUNT(*) FROM SYSIBMADM.SNAPLOCKWAIT
max_warning 5
max_critical 10
check_end

check_begin
name Lock waits (detail)
operation full
target SELECT AGENT_ID, LOCK_MODE, LOCK_OBJECT_TYPE FROM SYSIBMADM.SNAPLOCKWAIT
crontab */30 * * * *
check_end
```

| Clave | Obligatoria | Descripción |
|-------|-------------|-------------|
| `name` | Sí | Nombre del módulo. Una consulta sin él se omite |
| `target` | Sí | La consulta. Solo se aceptan sentencias que empiecen por `SELECT` (sin distinguir mayúsculas); cualquier otra se elimina y se informa en la información de la tarea |
| `operation` | No | `value` devuelve la primera columna de la primera fila como un único valor. Cualquier otro valor, o ninguno, devuelve todas las filas como texto |
| `datatype` | No | Tipo de módulo: `generic_data`, `generic_data_string` o `generic_proc`. Por defecto `generic_data_string`. Siempre `generic_data_string` cuando `operation` no es `value` |
| `description` | No | Descripción del módulo. Por defecto `Execution OK`, o el error de la base de datos si la consulta falla |
| `crontab` | No | Expresión cron de cinco campos que programa la consulta. Véase más abajo |
| `min_warning`, `max_warning`, `min_critical`, `max_critical` | No | Umbrales numéricos del módulo |
| `str_warning`, `str_critical` | No | Umbrales de texto del módulo |

Cuando `operation` devuelve todas las filas, cada fila pasa a ser una línea con sus columnas separadas por `|`. Un resultado vacío se publica como `No output.` en los módulos de texto.

La consola incluye dos consultas de ejemplo (`DB Blocks` y `Blocking elements`) ya cargadas en el cuadro **Custom queries**.

**Programación con `crontab`.** Una consulta con `crontab` solo se ejecuta cuando hay al menos una ocurrencia de la expresión pendiente desde su última ejecución correcta, y la hora de ejecución se conserva entre ejecuciones de la tarea. Una consulta que falla se reintenta en la siguiente ejecución de la tarea. La primera vez que se ve una consulta programada, solo cuenta una ocurrencia que caiga dentro del intervalo actual de la tarea, de modo que activar una programación diaria o mensual antigua no la ejecuta de inmediato. Una consulta programada que no toca no produce valor en esa ejecución, por lo que debe definir su módulo como asíncrono. Una expresión que no tiene cinco campos, o no es válida, se omite y se informa en la información de la tarea.

**Limitaciones conocidas de esta versión.** Considere que estas claves y marcadores no están disponibles:

- `target_databases` se lee, pero una consulta se ejecuta en todos los objetivos solo cuando se omite o vale `all`. Una lista de nombres de base de datos concretos hace que la consulta no se ejecute en ninguna.
- El marcador `$__self_dbname` mencionado en la ayuda de la consola se sustituye por una cadena vacía, no por el nombre de la base de datos.
- Las claves `unit`, `interval`, `parent`, `inverse_warning` e `inverse_critical` que aparecen en la ayuda de la consola no se aplican al módulo.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que se completa informa:

    - **Total agents**: agentes generados, uno por objetivo.
    - **Targets up**: objetivos a los que el addon se conectó.
    - **Targets down**: objetivos a los que no pudo conectar.

    Los errores de conexión se registran en la información de ejecución de la tarea.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea DB2 en Discovery con Total agents, Targets up y Targets down. -->

2. **Los agentes.** Uno por objetivo, con el nombre del objetivo o de la lista **Target agent**.

3. **Los módulos.** Todos los agentes tienen `DB2 connection`, con valor `1` si la conexión tuvo éxito. El resto de módulos aparecen solo si la conexión tuvo éxito; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Propiedad | Valor |
|-----------|-------|
| Nombre y alias del agente | La entrada de **Target agent** del objetivo, o la cadena del objetivo si no hay ninguna |
| Sistema operativo | `DB2` |
| Versión del sistema operativo | El nivel de servicio de la instancia leído de `SYSIBMADM.ENV_INST_INFO`; `Discovery` si no se pudo leer |
| Dirección | El host del objetivo |
| Grupo e intervalo | Los de la tarea de Discovery |

Cuando no se puede alcanzar un objetivo, su agente se genera igualmente con `DB2 connection` a `0` y ningún otro módulo.

### Módulos generados

Los nombres de módulo llevan el prefijo de **Custom module prefix** cuando se define.

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `DB2 connection` | `generic_proc` | Siempre | `1` si la conexión y una consulta de prueba tuvieron éxito, `0` en caso contrario |
| `AGENT_WAIT_TIME_PERCENT`, `CF_WAIT_TIME_PERCENT`, `IO_WAIT_TIME_PERCENT`, `LOCK_WAIT_TIME_PERCENT`, `NETWORK_WAIT_TIME_PERCENT`, `RECLAIM_WAIT_TIME_PERCENT`, `RQST_WAIT_TIME_PERCENT`, `ROUTINE_TIME_RQST_PERCENT`, `TOTAL_BP_HIT_RATIO_PERCENT`, `TRANSACT_END_PROC_TIME_PERCENT` | `generic_data` | **Get database summary** | Porcentajes de `MON_DB_SUMMARY`, unidad `%` |
| `APP_RQSTS_COMPLETED_TOTAL`, `AVG_RQST_CPU_TIME` | `generic_data` | **Get database summary** | Peticiones de aplicación completadas y tiempo medio de CPU por petición, de `MON_DB_SUMMARY` |
| `Log utilization percent` | `generic_data` | **Check transactional log utilization** | Porcentaje del log de transacciones en uso; la descripción indica los KB usados y disponibles |
| `Database size ` | `generic_data` | **Check DB size** | Suma de los tamaños de objetos de datos, índices, long, LOB y XML de todas las tablas, en `MB`. El nombre del módulo termina con un espacio |
| `Active connections` | `generic_data` | **Get number of connections** | Número de filas de `MON_CONNECTION_SUMMARY` |
| `cache hit ratio (<BUFFER_POOL>)` | `generic_data` | **Retrieve cache statistics** | Ratio de aciertos de índice de cada buffer pool, en `%`. El plugin define umbrales de advertencia y crítico por defecto en estos módulos; revíselos en la configuración del módulo |
| Sus consultas personalizadas | Según se defina | **Execute custom queries** | Un módulo por cada consulta que aplica y que toca ejecutarse |

Los grupos de resumen, log, tamaño, conexiones y caché son independientes: si se rechaza una consulta, faltan sus módulos pero los demás se crean igualmente.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. Recibe cuatro rutas de fichero e imprime un resultado JSON:

```bash
pandora_db2 --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> [--target_agents <PATH_TO_AGENTS>] [--custom_queries <PATH_TO_QUERIES>]
```

| Argumento | Obligatorio | Contenido |
|-----------|-------------|-----------|
| `--conf` | Sí | Fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion) |
| `--target_databases` | Sí | Objetivos, con el formato de **DB2 target strings** |
| `--target_agents` | No | Nombres de agente, con el formato de **Target agent** |
| `--custom_queries` | No | Consultas personalizadas, con el formato de **Custom queries** |

El resultado contiene un `summary` con `Total agents`, `Targets up` y `Targets down`, una clave `info` con mensajes cuando algo ha fallado, y `monitoring_data` con los agentes y módulos. El código de salida es `1` cuando falta un parámetro obligatorio, no se puede leer un fichero de entrada o falla un hilo de trabajo.

El fichero de configuración contiene la contraseña: protéjalo con permisos restrictivos.

### Notas de ejecución

- El addon elimina el contenido de su directorio de diagnóstico del cliente Db2 al comienzo de cada ejecución.
- Cada objetivo usa una conexión que se cierra cuando el objetivo ha sido procesado. El número de conexiones en paralelo nunca supera el número de objetivos.

## Solución de problemas

El addon no tiene indicador de modo detallado ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de ejecución, que se muestra en la información de ejecución de la tarea.

- **`Parameter [user] not defined`, `Parameter [password] not defined` o `Database targets not defined`**: falta un campo obligatorio. La tarea termina con código de salida `1` y no genera nada.
- **Un error de conexión y `Targets down` mayor que cero**: no se pudo alcanzar la base de datos. Compruebe el host, el puerto y el nombre de base de datos del objetivo, las credenciales y la ruta de red. El agente se genera igualmente con `DB2 connection` a `0`.
- **Un objetivo sin nombre de base de datos**: no puede conectar; use la forma `<HOST>:<PORT>/<DATABASE>`.
- **`DB2 error, please verify you have grants to ...`**: el usuario no puede leer la vista que usa esa opción (resumen, utilización del log, tamaño, número de conexiones o ratio de aciertos). Conceda `SELECT` sobre ella o desactive la opción.
- **`Removed [<query>] from custom queries, only select queries are allowed.`**: el `target` de una consulta personalizada no empieza por `SELECT`.
- **`Invalid custom query crontab expression`**: el `crontab` de una consulta no tiene cinco campos o no es válido; la consulta se omite.
- **Falta el módulo de una consulta personalizada**: la consulta no tiene `name` o `target`, tiene un `crontab` que no toca, o usa una lista en `target_databases` (consulte [Consultas personalizadas](#consultas-personalizadas)).
- **`Failed to execute query: ...` en la descripción de un módulo**: la base de datos rechazó la consulta personalizada.
- **`Can't update custom query crontab state`**: el addon no puede escribir el estado de la programación, por lo que la consulta programada puede volver a ejecutarse en la siguiente ejecución.
- **`Error while runing single thread`**: un error inesperado detuvo un hilo de trabajo; el código de salida es `1`.

## Referencia

### Parámetros de la tarea

#### DB2 Base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| DB2 target strings | `_dbstrings_` | área de texto | vacío | Obligatorio. `SERVER:PORT/DATABASE`, separados por comas o uno por línea; `#` inicia una línea de comentario |
| User | `_dbuser_` | cadena | vacío | Obligatorio |
| Password | `_dbpass_` | contraseña | vacío | Obligatorio |

#### DB2 Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Max threads | `_threads_` | número | `1` | Opcional. Los objetivos se reparten entre los hilos; nunca más hilos que objetivos |
| Target agent | `_engineAgent_` | cadena | vacío | Opcional. Nombres de agente separados por comas, en el orden de los objetivos. Vacío usa la cadena del objetivo |
| Custom module prefix | `_prefixModuleName_` | cadena | vacío | Opcional. Se antepone a todos los nombres de módulo |
| Get database summary | `_checkDbSummary_` | casilla | activada | Módulos de resumen |
| Check transactional log utilization | `_checkTransactionalLogUtilization_` | casilla | activada | `Log utilization percent` |
| Get number of connections | `_checkConnections_` | casilla | activada | `Active connections` |
| Check DB size | `_checkDbSize_` | casilla | activada | `Database size ` |
| Retrieve cache statistics | `_checkCache_` | casilla | activada | Módulos `cache hit ratio` |
| Execute custom queries | `_executeCustomQueries_` | casilla | activada | Ejecuta las consultas personalizadas |
| Custom queries | `_customQueries_` | área de texto | Dos consultas de ejemplo | Opcional. Se muestra cuando **Execute custom queries** está activada |

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no es un número se lee como `0`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_id` | `10` | ID del grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `user` | vacío | Usuario de Db2. Obligatorio |
| `password` | vacío | Contraseña de Db2. Obligatoria |
| `threads` | `1` | Número de hilos en paralelo |
| `modules_prefix` | vacío | Prefijo de todos los nombres de módulo |
| `execute_custom_queries` | `1` | Ejecutar consultas personalizadas |
| `analyze_connections` | `1` | Módulo `Active connections` |
| `cache_stats` | `1` | Módulos de ratio de aciertos de caché |
| `database_summary` | `1` | Módulos de resumen |
| `transactional_log` | `1` | Módulo de utilización del log |
| `db_size` | `1` | Módulo de tamaño de la base de datos |
| `cron_state_dir` | `pandora_db2_cron_state` en el directorio temporal del sistema | Directorio donde se guardan las horas de ejecución de las consultas personalizadas programadas |

Ejemplo:

```ini
agents_group_id        = 10
interval               = 300
user                   = <DB2_USER>
password               = <DB2_PASSWORD>
threads                = 2
modules_prefix         = db2_
execute_custom_queries = 1
analyze_connections    = 1
cache_stats            = 1
database_summary       = 1
transactional_log      = 1
db_size                = 1
```

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.db2` |
| Nombre | DB2 |
| Versión | `1.2` |
| Última actualización en el Marketplace | 2026-08-28 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
