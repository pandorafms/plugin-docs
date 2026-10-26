# SAP HANA Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El plugin de Discovery de SAP HANA se conecta a una o varias bases de datos SAP HANA, ejecuta un conjunto de consultas SQL sobre las vistas del sistema y convierte los resultados en módulos de monitorización de Pandora FMS. De serie cubre disponibilidad, versión, memoria, conexiones, transacciones, estimación del tamaño de backups, E/S, CPU, licencia, fragmentación del row store, volúmenes y estadísticas por servicio. Cada grupo se activa o desactiva desde la tarea. Además puede añadir módulos propios basados en SQL.

El plugin crea **un agente por cada destino SAP HANA**, con un módulo de disponibilidad y un módulo por cada métrica habilitada. Una misma tarea de Discovery puede listar varios destinos, de modo que una sola tarea cubre todo un conjunto de bases de datos.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Versión `1.0` del add-on (`pandorafms.sap.hana`) | Objetivo documentado | Versión publicada en la entrada del Marketplace, actualizada por última vez el 2026-06-11. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Pandora FMS NG 784 y posteriores | `Supported` | Declaración mostrada en el Marketplace para todas sus integraciones |
| Puerto SQL de SAP HANA accesible desde el servidor Discovery | `Required` | El plugin abre una conexión a la base de datos por destino |
| Usuario de base de datos con lectura de las vistas de monitorización `SYS` | `Required` | Prerrequisito, no una declaración de compatibilidad. Consulte [Prerrequisitos](#prerrequisitos) |
| Cualquier versión concreta de SAP HANA | `Not validated` | No se ha registrado ninguna matriz de versiones o ediciones |

Según su entrada del Marketplace, la descarga del add-on está limitada a usuarios con licencia. Esta página no describe más condiciones de licencia.

### Prerrequisitos

1. **Acceso de red** desde la máquina que ejecuta la tarea de Discovery hasta el puerto SQL de cada destino SAP HANA.
2. **Un usuario y una contraseña de base de datos** de SAP HANA. Las comprobaciones integradas del plugin solo ejecutan sentencias `SELECT`, sobre estas vistas del sistema: `SYS.M_DATABASE`, `SYS.M_HOST_RESOURCE_UTILIZATION`, `SYS.M_SERVICE_STATISTICS`, `SYS.M_CONNECTIONS`, `SYS.M_BLOCKED_TRANSACTIONS`, `SYS.M_TRANSACTIONS`, `SYS.M_VOLUMES`, `SYS.M_VOLUME_IO_TOTAL_STATISTICS`, `SYS.M_RS_MEMORY`, `SYS.M_CONVERTER_STATISTICS` y `SYS.M_LICENSE`. El usuario debe poder leer las vistas de los grupos que habilite; no se documenta un conjunto de privilegios más reducido. Una vista que el usuario no puede leer genera un módulo con valor vacío en lugar de hacer fallar toda la tarea.
3. **Una credencial de Pandora FMS de tipo Custom** en el almacén de credenciales, con ese usuario y contraseña. Ambos son obligatorios.
4. **Pandora FMS**: un servidor Discovery que ejecute la tarea y la consola para definirla.

El plugin se distribuye como un paquete autocontenido, por lo que no hay que instalar nada más en el servidor Discovery.

### Instalar el plugin

Cargue el paquete `.disco` desde el Marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/entries/pandorafms.sap.hana](https://marketplace.pandorafms.com/entries/pandorafms.sap.hana)

Una vez cargado, la aplicación **SAP HANA** está disponible al crear tareas de Discovery.

### Crear la credencial

1. En la consola de Pandora FMS, abra el almacén de credenciales y cree una credencial nueva de tipo **Custom**.
2. Introduzca el **usuario** y la **contraseña** de SAP HANA.
3. Asígnele un identificador que reconozca al elegirla en la tarea.

<!-- SCREENSHOT NEEDED: Formulario del almacén de credenciales para una credencial Custom con usuario y contraseña de ejemplo, sin secretos reales, que muestre cómo se crea la credencial de SAP HANA. -->

La credencial se guarda en la consola y la tarea la referencia, de modo que la contraseña no se escribe en los campos de la tarea.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Application → SAP HANA**. La consola presenta los campos en dos pasos, y todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

![Página de aplicaciones de Discovery con la aplicación SAP HANA seleccionada](../assets/images/discovery/sap-hana/sap-hana-applications-menu.png)

1. **SAP HANA Base** — los destinos y cómo autenticarse:

    - **SAP HANA target strings**: un destino por línea, o varios separados por comas, con el formato `HOST:PORT\DATABASE`. Las líneas que empiezan por `#` son comentarios. **Cada destino válido genera un agente.**
    - **HANA Credentials**: la credencial Custom creada antes.

    ![Paso SAP HANA Base del asistente con el campo de destinos y el selector HANA Credentials](../assets/images/discovery/sap-hana/sap-hana-base-step.png)

2. **SAP HANA Detailed** — ajuste opcional del resultado:

    - **Max threads** y **Target agent**.
    - **Regexp to filter modules** con **Allow regexp**, y **Regexp to discard modules** con **Deny regexp**.
    - Una casilla por cada grupo de métricas integrado. Los valores por defecto figuran en [Parámetros de la tarea](#parametros-de-la-tarea).
    - **Execute custom queries** y **Custom queries**.
    - **Custom module prefix**.
    - **Custom modules (legacy)**.

    <!-- SCREENSHOT NEEDED: Paso SAP HANA Detailed del asistente con las casillas de los grupos de métricas, los filtros por expresión regular y el área de custom queries. -->

El grupo de agentes y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes y módulos que crea el plugin.

### Formato del destino

Un destino se escribe como `HOST:PORT\DATABASE`, por ejemplo:

```
<HANA_HOST_1>:<SQL_PORT>\<DATABASE_NAME>
<HANA_HOST_2>:<SQL_PORT>\<DATABASE_NAME>
# <HANA_HOST_3>:<SQL_PORT>\<DATABASE_NAME>
```

- `HOST` puede ser un nombre o una dirección IP. Un nombre debe resolverse desde el servidor Discovery.
- `PORT` es el puerto SQL numérico de la instancia o base de datos. Es obligatorio.
- `DATABASE` se pasa a SAP HANA como el nombre de la base de datos a la que conectar.
- Antes del nombre de la base de datos también se acepta `:` en lugar de `\`.

Una línea que no cumple este formato no se monitoriza y se cuenta en **Targets down**. Consulte [Solución de problemas](#solucion-de-problemas).

### Asignar nombres de agente a los destinos

Por defecto cada agente se llama `HOST - DATABASE`. Para elegir los nombres, rellene **Target agent** con un nombre de agente por línea, **en el mismo orden** que los destinos. Una línea en blanco deja a ese destino con su nombre por defecto. El nombre se usa como nombre y como alias del agente.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** La ejecución informa de:

    - **Total agents**: agentes generados por la tarea.
    - **Targets up**: destinos a los que el plugin se conectó.
    - **Targets down**: destinos que no se pudieron monitorizar.

    Espere un agente por cada destino válido y accesible. Cada destino fallido añade una línea a la información de ejecución con su host, puerto, base de datos y el motivo.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea de Discovery de SAP HANA que muestre Total agents, Targets up y Targets down. -->

2. **Los agentes.** Uno por destino, con la dirección fijada al host del destino y el sistema operativo fijado a `SAP HANA`.

    ![Lista de agentes con un agente creado por la tarea de SAP HANA, llamado HOST - DATABASE](../assets/images/discovery/sap-hana/sap-hana-agent-list.png)

3. **Los módulos de cada agente.** Con las opciones por defecto, un destino accesible produce:

    | Módulo | Valor esperado |
    |--------|----------------|
    | `hana_availability` | `1` — el plugin se conectó a la base de datos |
    | `version` | Cadena con la versión de SAP HANA |
    | `backups_estimated_size_bytes` | Tamaño estimado en bytes |
    | `connections_total`, `connections_running`, `connections_idle` | Recuentos de conexiones |
    | `memory_used_bytes`, `memory_allocation_limit_bytes` | Memoria en bytes |
    | `blocked_transactions`, `open_transactions` | Recuentos de transacciones |

    Los nombres de módulo llevan el **Custom module prefix** cuando se definió, y los filtros por expresión regular pueden eliminar cualquier módulo salvo `hana_availability`.

Si la tarea no informa de ningún agente, revise **Targets down** y la información de ejecución, y siga [Solución de problemas](#solucion-de-problemas).

## Interpretar los resultados

### Agentes y módulos generados

El plugin crea **un agente por cada destino**. El nombre y el alias del agente son `HOST - DATABASE`, o el nombre indicado en **Target agent**. Dos destinos que resuelvan al mismo nombre reportan al mismo agente.

`hana_availability` es un módulo `generic_proc` con valor `1` siempre que el plugin se conectó al destino. Se crea siempre para un destino accesible y no le afectan las expresiones allow o deny. Un destino inaccesible no crea agente ni valor `0`: solo se informa en la información de ejecución y en **Targets down**.

Cuando una consulta falla o la vista no existe en ese entorno SAP HANA, el módulo se crea igualmente con valor vacío. Por lo demás, los módulos de métricas son `generic_data` (números) o `generic_data_string` (texto).

### Grupos de módulos

Los grupos siguientes se activan con las casillas de la tarea. Los módulos exactos de cada grupo figuran en [Agentes y módulos](#agentes-y-modulos).

| Grupo (casilla) | Por defecto | Qué aporta |
|-----------------|-------------|------------|
| Enable Backups Size | Activado | Tamaño estimado de backups en bytes |
| Enable Timestamp | Desactivado | Marca de tiempo UTC actual de la base de datos |
| Enable Hana Version | Activado | Versión de SAP HANA |
| Enable Data Disk Information | Desactivado | Número de volúmenes y de entradas de E/S de volumen |
| Enable Hana Service Statistics | Desactivado | Estado, memoria, CPU, peticiones e hilos de cada servicio |
| Enable Hana CPU Time | Desactivado | Tiempo de CPU agregado de los servicios |
| Enable Hana RS Fragmentation | Desactivado | Porcentaje de fragmentación del row store |
| Enable Hana License | Desactivado | Registros de licencia, fecha de expiración y uso |
| Enable Hana IO Stats | Desactivado | Bytes leídos y escritos acumulados, y tiempo de E/S |
| Enable Hana Get Stated Connections | Activado | Conexiones totales, en ejecución e inactivas |
| Enable Hana Memory | Activado | Memoria usada y límite de asignación |
| Enable Hana Transactions | Activado | Transacciones bloqueadas y abiertas |

## Operar

### Custom queries

Con **Execute custom queries** habilitado, puede definir módulos adicionales como consultas SQL en **Custom queries**. La tarea se entrega con una plantilla comentada del formato. Cada módulo es un bloque `check_begin` / `check_end`, con un par `clave valor` por línea:

```
check_begin
name custom_running_connections
description Connections in RUNNING state
operation value
target SELECT COUNT(*) FROM SYS.M_CONNECTIONS WHERE CONNECTION_STATUS = 'RUNNING'
datatype generic_data
unit conns
check_end

check_begin
name custom_service_status
description Status of every service
operation full
target SELECT HOST, SERVICE_NAME, ACTIVE_STATUS FROM SYS.M_SERVICE_STATISTICS
datatype generic_data_string
check_end
```

Estos ejemplos se comprobaron contra el analizador del plugin; no se ejecutaron contra un sistema SAP HANA real.

Reglas:

- `name`, `target` y `datatype` son obligatorios en cada bloque. Un bloque que no los tenga se ignora.
- `target` debe ir en una sola línea. Se omiten las líneas en blanco y las que empiezan por `#`.
- `operation value` (por defecto) toma la primera columna de la primera fila. Si la consulta no devuelve filas o devuelve un nulo, el valor es `0`. `operation full` devuelve todas las filas como texto, con las columnas unidas por `;` y las filas por saltos de línea: un `datatype` `generic_data` se convierte en `generic_data_string`.
- `$__self_dbname` en la consulta se sustituye por el nombre de la base de datos del destino consultado.
- Por defecto un bloque se ejecuta en todos los destinos. Límitelo con `target_instances` (valores `HOST:PORT` separados por comas, escritos exactamente como en el destino), `target_databases` e `ignore_databases`. `target_scope` selecciona qué filtros se aplican: `instances` aplica solo el filtro de instancias, `databases` aplica solo los filtros de bases de datos y `all` (por defecto) aplica ambos.
- Una consulta fallida crea igualmente el módulo, con valor vacío.
- Los módulos personalizados están sujetos a **Custom module prefix** y a las expresiones allow y deny.

La plantilla también lista las claves `min_warning`, `max_warning`, `min_critical`, `max_critical`, `inverse_warning`, `inverse_critical`, `str_warning`, `str_critical`, `interval` y `parent`. La versión actual las lee pero no las aplica a los módulos creados, así que configure después umbrales e intervalos en los módulos desde la consola.

### Módulos personalizados heredados

**Custom modules (legacy)** acepta un módulo por línea con el formato:

```
module_name:SQL_query:datatype:description
```

`datatype` debe ser `generic_data`, `generic_data_string` o `generic_proc`; `description` es opcional. La consulta puede contener a su vez caracteres `:`. Estos módulos se crean aunque **Execute custom queries** esté desactivado. Use custom queries para las definiciones nuevas.

### Limitaciones

- La tarea acepta el valor de `Max threads`, pero en esta versión no cambia cómo se procesan los destinos: se consultan uno tras otro.
- La conexión usa el usuario y la contraseña de la credencial. El plugin no tiene ningún campo para seleccionar opciones de cifrado.

## Solución de problemas

La tarea no tiene opción de depuración. Su canal de diagnóstico es el resumen y la información de ejecución de la tarea de Discovery.

- **`Missing required parameters`** — la credencial no tiene usuario o contraseña, o la lista de destinos está vacía tras quitar los comentarios. El resumen indica cuál falta.
- **`No agents generated`** — no se pudo monitorizar ningún destino. Lea las líneas `Target down` de la información de ejecución.
- **`Target down HOST:PORT\DATABASE - Cannot resolve hostname`** — el servidor Discovery no resuelve el nombre. Use una dirección IP o corrija la resolución DNS.
- **`Target down ... - SAP HANA connection failed: ...`** — la base de datos rechazó la conexión o las credenciales. Revise el puerto, el nombre de la base de datos, el usuario y la contraseña, y que el servidor Discovery alcance el puerto SQL.
- **Targets down es mayor que los fallos listados** — una línea que no sigue `HOST:PORT\DATABASE` se cuenta como caída sin mensaje. Revise el formato de cada destino.
- **Existe un módulo con valor vacío** — falló la consulta que lo alimenta o la vista no está disponible en ese entorno SAP HANA, por ejemplo porque el usuario no puede leerla. Ejecute el mismo `SELECT` con ese usuario para ver el error de la base de datos.
- **Faltan módulos esperados** — una **Allow regexp** o una **Deny regexp** los eliminó. Las expresiones se buscan en cualquier parte del nombre del módulo (incluido el prefijo), y una expresión no válida se ignora sin avisar.
- **No aparecen métricas de otro grupo** — solo los grupos con su casilla habilitada crean módulos. Consulte [Grupos de módulos](#grupos-de-modulos).

## Referencia

### Parámetros de la tarea

#### SAP HANA Base

| Campo | Obligatorio | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| SAP HANA target strings (`_dbstrings_`) | Sí | — | Destinos como `HOST:PORT\DATABASE`, uno por línea o separados por comas. `#` inicia una línea de comentario. |
| HANA Credentials (`_credentials_`) | Sí | — | Credencial Custom con el usuario y la contraseña. |

#### SAP HANA Detailed

| Campo | Obligatorio | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| Max threads (`_threads_`) | No | `1` | La tarea lo acepta; sin efecto en el procesamiento en esta versión. |
| Target agent (`_targetAgent_`) | No | vacío | Un nombre de agente por destino, en el mismo orden. Vacío: `HOST - DATABASE`. |
| Regexp to filter modules (`_regexpFilter_`) | No | Desactivado | Muestra **Allow regexp**. |
| Allow regexp (`_allowRegexp_`) | No | vacío | Solo se crean los módulos cuyo nombre coincide. |
| Regexp to discard modules (`_regexpDiscard_`) | No | Desactivado | Muestra **Deny regexp**. |
| Deny regexp (`_denyRegexp_`) | No | vacío | No se crean los módulos cuyo nombre coincide. |
| Enable Backups Size | No | Activado | Consulte [Agentes y módulos](#agentes-y-modulos). |
| Enable Timestamp | No | Desactivado | |
| Enable Hana Version | No | Activado | |
| Enable Data Disk Information | No | Desactivado | |
| Enable Hana Service Statistics | No | Desactivado | |
| Enable Hana CPU Time | No | Desactivado | |
| Enable Hana RS Fragmentation | No | Desactivado | |
| Enable Hana License | No | Desactivado | |
| Enable Hana IO Stats | No | Desactivado | |
| Enable Hana Get Stated Connections | No | Activado | |
| Enable Hana Memory | No | Activado | |
| Enable Hana Transactions | No | Activado | |
| Execute custom queries (`_executeCustomQueries_`) | No | Activado | Muestra **Custom queries**. |
| Custom queries (`_customQueries_`) | No | Plantilla comentada | Bloques `check_begin` / `check_end`. Consulte [Custom queries](#custom-queries). |
| Custom module prefix (`_prefixModuleName_`) | No | vacío | Texto antepuesto al nombre de cada módulo que crea la tarea. |
| Custom modules (legacy) | No | vacío | Líneas `module_name:SQL_query:datatype:description`. |

El grupo de agentes y el intervalo de los módulos proceden de la definición genérica de la tarea.

### Agentes y módulos

El prefijo se muestra como `<prefix>` y está vacío salvo que se defina **Custom module prefix**. Las unidades son las que informa el plugin.

| Módulo | Tipo | Condición |
|--------|------|-----------|
| `<prefix>hana_availability` | `generic_proc` | Siempre, para un destino accesible |
| `<prefix>backups_estimated_size_bytes` | `generic_data` (bytes) | Backups Size. Suma del tamaño de página asignado de las estadísticas del conversor; es una estimación de mejor esfuerzo y no el tamaño de los ficheros de backup |
| `<prefix>timestamp` | `generic_data_string` | Timestamp. Marca de tiempo UTC actual de la base de datos |
| `<prefix>version` | `generic_data_string` | Hana Version |
| `<prefix>volumes_count` | `generic_data` | Data Disk Information. Número de volúmenes |
| `<prefix>volumes_io_entries` | `generic_data` | Data Disk Information. Número de entradas de E/S de volumen |
| `<prefix>rowstore_fragmentation_pct` | `generic_data` (%) | RS Fragmentation. Tamaño libre sobre asignado del row store |
| `<prefix>io_total_read_bytes` | `generic_data` (bytes) | IO Stats. Lectura acumulada |
| `<prefix>io_total_write_bytes` | `generic_data` (bytes) | IO Stats. Escritura acumulada |
| `<prefix>io_total_time_ms` | `generic_data` (ms) | IO Stats. Tiempo total de E/S |
| `<prefix>memory_used_bytes` | `generic_data` (bytes) | Memory |
| `<prefix>memory_allocation_limit_bytes` | `generic_data` (bytes) | Memory |
| `<prefix>cpu_total_time_ms` | `generic_data` (ms) | CPU Time. Tiempo total de CPU agregado de los servicios |
| `<prefix>cpu_process_time_ms` | `generic_data` (ms) | CPU Time. Tiempo de CPU de proceso agregado de los servicios |
| `<prefix>license_count` | `generic_data` | License, cuando existe la vista de licencia |
| `<prefix>license_expiration_date` | `generic_data_string` | License, cuando existe la vista de licencia |
| `<prefix>license_usage_memory_gb` | `generic_data` (GB) | License, cuando existe la vista de licencia. Valor de mejor esfuerzo del uso de licencia |
| `<prefix>license_status` | `generic_data_string` | License, solo cuando no existe la vista de licencia; valor vacío |
| `<prefix>connections_total` | `generic_data` (conns) | Get Stated Connections |
| `<prefix>connections_running` | `generic_data` (conns) | Get Stated Connections. Estado `RUNNING` |
| `<prefix>connections_idle` | `generic_data` (conns) | Get Stated Connections. Estado `IDLE` |
| `<prefix>blocked_transactions` | `generic_data` | Transactions |
| `<prefix>blocked_transactions_distinct_users` | `generic_data` | Transactions, solo cuando la vista de transacciones bloqueadas expone una columna de usuario |
| `<prefix>open_transactions` | `generic_data` | Transactions, solo cuando existe la vista de transacciones |

#### Estadísticas de servicio

Con **Enable Hana Service Statistics** se crea un conjunto de módulos por host y servicio, llamados `<prefix><host>.<service>-<COLUMN>`. Solo se crean las columnas que existen en ese entorno SAP HANA.

| Columna | Tipo | Notas |
|---------|------|-------|
| `ACTIVE_STATUS` | `generic_proc` | `1` para `YES`, `TRUE`, `1`, `ACTIVE` o `RUNNING`; en otro caso `0` |
| `PROCESS_CPU_TIME`, `TOTAL_CPU_TIME` | `generic_data` | |
| `PROCESS_MEMORY`, `TOTAL_MEMORY`, `AVAILABLE_MEMORY` | `generic_data` | |
| `ACTIVE_REQUEST_COUNT`, `PENDING_REQUEST_COUNT` | `generic_data` | |
| `ACTIVE_THREAD_COUNT`, `THREAD_COUNT`, `OPEN_FILE_COUNT` | `generic_data` | |
| `REQUESTS_PER_SEC`, `RESPONSE_TIME` | `generic_data` | |
| `START_TIME`, `SYS_TIMESTAMP` | `generic_data` (`_timeticks_`) | Tiempo transcurrido desde esa marca de tiempo, en timeticks |

Si la vista de estadísticas de servicio no tiene las columnas de host o de nombre de servicio, se crea en su lugar un único módulo `service_statistics` vacío.

### Propiedades del agente

| Propiedad | Valor |
|-----------|-------|
| Nombre y alias del agente | `HOST - DATABASE`, o el valor de **Target agent** |
| Dirección | Host del destino |
| Sistema operativo | `SAP HANA` |
| Grupo e intervalo | De la tarea de Discovery |

### Salida de la ejecución

La ejecución informa de `Total agents`, `Targets up` y `Targets down`. La ejecución termina en estado de error cuando faltan parámetros obligatorios, cuando falla la lectura de la configuración o cuando no se generó ningún agente.

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la app | `pandorafms.sap.hana` |
| Versión del add-on | `1.0` |
| Paquete del Marketplace | `pandorafms.sap.hana.1.0.disco` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
