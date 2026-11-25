# IBM Informix Discovery

*Última actualización del artículo: 2026-11-25.*

## Qué monitoriza

El addon de Discovery de IBM Informix monitoriza instancias de IBM Informix de forma remota. Una tarea de Discovery se conecta por TCP/IP a la pseudo-base de datos `sysmaster` de cada instancia indicada en la tarea y convierte el resultado en agentes y módulos de Pandora FMS. No se instala nada en el servidor de base de datos.

El addon cubre:

- **Espacio y almacenamiento:** cada dbspace se descubre automáticamente, con porcentaje de uso, espacio libre y usado, estado de los chunks y estado de los logical logs.
- **Memoria compartida y buffer pool:** ratios de acierto de lectura y escritura, esperas de buffers y contadores crudos de lectura/escritura.
- **Bloqueos y concurrencia:** esperas de lock, deadlocks, timeouts de lock, desbordamientos de tablas y número de sesiones y locks activos.
- **Checkpoints e I/O:** duración, tiempo de bloqueo y razón del último checkpoint, foreground writes e I/O opcional por dbspace.
- **Consultas y recursos:** sequential scans, sorts, modo del motor y tablas más activas.

Una tarea de Discovery crea **un agente por cada instancia Informix**. Cada instancia genera un módulo por cada dbspace descubierto más las familias de métricas que active, de forma que una tarea con dos instancias y tres dbspaces en cada una crea dos agentes con un conjunto independiente de módulos por dbspace.

El addon también proporciona una vista de consola opcional, **Monitoring → IBM Informix**, que agrupa los módulos generados por agente y permite filtrar por agente, categoría de métrica, dbspace, nombre de módulo y estado.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.informix`, versión `1.0` | Objetivo documentado | La versión que describe esta página |
| Acceso de red desde el servidor de Discovery a cada listener de Informix (TCP, puerto por defecto `9088`) | `Requerido` | El addon se conecta por TCP/IP |
| Un usuario de Informix con los permisos de [Usuario de base de datos](#usuario-de-base-de-datos) | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Informix 12.10 y 14.10 | `Objetivo documentado` | Las vistas de `sysmaster` que usa el addon están documentadas para ambas ramas; no se ha registrado una matriz de instancias reales para esta versión |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado una matriz de sistemas operativos para este addon |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a cada listener de Informix que quiera monitorizar.
2. **Un usuario y una contraseña de Informix** con acceso `SELECT` a las vistas de `sysmaster` indicadas en [Usuario de base de datos](#usuario-de-base-de-datos). Las mismas credenciales se usan para todos los objetivos de la tarea.
3. **El driver Python de Informix.** El addon usa `IfxPy` y el runtime del IBM Informix Client SDK. El usuario y la contraseña de Informix se leen de una entrada personalizada del almacén de credenciales de Pandora FMS. En las plataformas donde el wheel de `IfxPy` no incluye el Client SDK, instale el IBM Informix Client SDK en el servidor de Discovery y deje `INFORMIXDIR` disponible para el proceso del plugin.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

### Usuario de base de datos

El addon solo lee vistas SMI. Conceda `SELECT` sobre las vistas de las familias que active:

| Familia | Vistas leídas |
|---------|---------------|
| Motor | `sysshmvals`, `sysmachineinfo`, `sysvpprof`, `systables` (`DBINFO`) |
| Espacio y logical logs | `sysdbspaces`, `syschunks`, `syslogs` |
| Buffer pool, locks, checkpoints, consultas | `sysprofile`, `syscheckpoint`, `syssessions`, `syslocks` |
| Tablas más activas | `sysptprof` |
| I/O por dbspace | `syschkio` |

La contraseña se escribe en el fichero de configuración temporal de la tarea en el servidor de Discovery mientras esta se ejecuta. Use un usuario dedicado de solo lectura para Pandora FMS.

### Instalar el addon

Instale el paquete `.disco` `pandorafms.informix` desde **Discovery → Manage disco packages**, o desde su entrada del Marketplace cuando esté publicada.

Una vez cargado, **IBM Informix** está disponible al crear tareas de Discovery de tipo aplicación.

<!-- SCREENSHOT NEEDED: Lista de aplicaciones de Discovery con la entrada IBM Informix una vez cargado el paquete. -->

## Configurar la tarea de Discovery

Cree una tarea desde **Discovery → Applications → IBM Informix**. La consola presenta la tarea en cuatro pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

### 1. Definición de la tarea

Complete el nombre de la tarea, la descripción, el servidor de Discovery, el grupo de destino y el intervalo. El grupo y el intervalo se aplican a los agentes que crea la tarea. El timeout de ejecución debe ser mayor que el **Max execution time** del addon.

<!-- SCREENSHOT NEEDED: Paso de definición de la tarea con el nombre, el grupo y el intervalo cumplimentados. -->

### 2. Conexión Informix

![Paso de conexión con los objetivos, el selector del almacén de credenciales y los selectores de timeout de conexión, consulta y ejecución máxima.](../assets/images/discovery/informix/task-connection.png)

- **Targets**: las instancias a monitorizar, una por entrada. Consulte [Formato de objetivo](#formato-de-objetivo).
- **Informix credentials**: seleccione una credencial personalizada del almacén de credenciales de Pandora FMS. Debe contener el usuario y la contraseña de Informix. El usuario solo necesita permisos `SELECT` sobre `sysmaster`.
- **Connection timeout**, **Query timeout** y **Max execution time**: cuánto puede dedicar el addon a conectar, ejecutar cada consulta y completar la ejecución. Consulte [Timeouts](#timeouts).

### 3. Colecciones

![Paso de colecciones con las familias de métricas, el límite de tablas y el interruptor de I/O por dbspace.](../assets/images/discovery/informix/task-collections.png)

Active o desactive cada familia de métricas. Todas están activas por defecto salvo **Per-dbspace I/O**:

- **Engine status and version**
- **Space and logical logs**
- **Buffer pool**
- **Locks and concurrency**
- **Checkpoints and I/O waits**
- **Queries and resources**
- **Active sessions**
- **Top active tables**, con el límite **Top tables**
- **Per-dbspace I/O**

El estado de la conexión se informa siempre, aunque una familia esté desactivada, para que una instancia caída siga siendo visible. El estado del motor se informa cuando la familia del motor está activa.

### 4. Salida y filtros

![Paso de salida y filtros con los prefijos de alias y módulo, las listas de permitidos y denegados y la configuración de Tentacle.](../assets/images/discovery/informix/task-output.png)

- **Agent alias prefix**: texto que se añade delante del alias de cada agente generado.
- **Module name prefix**: texto que se añade delante de cada nombre de módulo.
- **Allow list** y **Deny list**: expresiones regulares aplicadas al nombre final del módulo. La lista de permitidos se aplica primero; si está vacía, se permiten todos los módulos. La lista de denegados se aplica después.
- **Transfer mode**: `native` (por defecto) usa el flujo JSON de Discovery; `tentacle` genera ficheros XML y los transfiere a un servidor Tentacle.
- **Tentacle address** y **Tentacle port**: solo se usan cuando el modo de transferencia es `tentacle`.

### Formato de objetivo

Cada objetivo identifica un host, un puerto opcional y un nombre de servidor Informix opcional:

| Forma | Host | Puerto | Servidor |
|-------|------|--------|----------|
| `<HOST>:<PORT>/<SERVER>` | `<HOST>` | `<PORT>` | `<SERVER>` |
| `<HOST>/<SERVER>` | `<HOST>` | `9088` | `<SERVER>` |
| `<HOST>:<PORT>` | `<HOST>` | `<PORT>` | Lo resuelve el Client SDK |
| `<HOST>` | `<HOST>` | `9088` | Lo resuelve el Client SDK |

`SERVER` es el `DBSERVERNAME` de Informix. Cuando se omite, el Client SDK resuelve un alias de `SQLHOSTS` que coincida. Las líneas que empiezan por `#` son comentarios.

Ejemplo para dos instancias:

```text
# Producción
<INFORMIX_HOST_1>:9088/<SERVER_1>
<INFORMIX_HOST_2>:9088/<SERVER_2>
```

### Timeouts

Los tres campos de timeout son selectores de tiempo: elija un periodo predefinido o — como administrador — use el control de edición (lápiz) para introducir una cantidad y una unidad personalizadas. El addon lee el valor en segundos.

| Campo | Por defecto | Límites |
|-------|-------------|---------|
| **Connection timeout** | `20` segundos | Establecer la conexión con cada instancia |
| **Query timeout** | `120` segundos | Cada consulta SQL individual |
| **Max execution time** | `240` segundos | La ejecución completa, contando todos los objetivos |

- **Connection timeout.** Un objetivo que no conecta dentro de este tiempo se informa en **Targets down** y su agente se crea con `Connection status` a `0`.
- **Query timeout.** Una consulta que no termina a tiempo se informa en la información de la tarea y el addon continúa con la siguiente familia.
- **Max execution time.** Cuando se agota el presupuesto, se omiten las familias pendientes y los objetivos restantes y se devuelven los datos recogidos hasta ese momento. Use `0` para desactivarlo.

Mantenga **Max execution time** por debajo del timeout de la tarea de Discovery. Si se alcanza antes el timeout de la tarea, Pandora FMS detiene el addon con `SIGTERM` y la ejecución termina con los datos parciales recogidos hasta ese momento.

## Verificación

Tras la primera ejecución, el resumen de la tarea informa de:

| Campo del resumen | Significado |
|-------------------|-------------|
| **Total agents** | Número de instancias Informix que generaron un agente |
| **Total modules** | Número de módulos creados en la ejecución |
| **Targets processed** | Objetivos analizados e intentados |
| **Targets down** | Objetivos que no se pudieron conectar o no generaron módulos |
| **Errors** | Errores de consulta o transferencia registrados en la información de la tarea |

La información de la tarea también contiene el detalle de error de cada objetivo, sin escribir la contraseña.

Una ejecución correcta crea un agente por instancia. El alias del agente es la cadena del objetivo (o el prefijo de alias más la cadena del objetivo) y el nombre del agente es un hash MD5. El agente guarda el identificador de su instancia en `extra_data`:

```text
informix:agent:<instance>
```

El identificador de instancia es el objetivo normalizado, por ejemplo `10.0.0.11_9088_ifxprod`.

## Entender los resultados

### Identidad y cardinalidad del agente

- Un agente por instancia. La misma instancia listada dos veces en la misma tarea no se deduplica en el addon; liste cada instancia una sola vez.
- El nombre del agente es estable para el mismo alias. Cambiar el **Agent alias prefix** cambia el alias y el nombre del agente generado.
- Cada módulo lleva un marcador estable en `extra_data`. El segundo token es la familia de métrica y el resto identifica el recurso:

```text
informix:engine:<metric>
informix:dbspace:<dbspace>
informix:storage:<metric>
informix:buffers:<metric>
informix:locks:<metric>
informix:sessions:<metric>
informix:checkpoints:<metric>
informix:queries:<metric>
informix:tables:<database>.<table>
informix:io:<dbspace>
```

### Grupos de módulos

| Grupo | Qué muestra | Notas |
|-------|-------------|-------|
| Motor | Estado de conexión, estado del motor, modo, versión, uptime, host y virtual processors | `Informix engine status` vale `1` solo cuando `sh_mode` informa On-Line |
| Dbspaces | Un conjunto de módulos por dbspace descubierto: uso %, MB libres, MB usados, MB totales y chunks | El uso avisa al `80%` y es crítico al `90%` |
| Almacenamiento y logs | Chunks offline o inconsistentes, logical logs libres, logs sin respaldar, porcentaje usado y logs actuales | Menos de tres logs libres avisa; cero logs libres es crítico |
| Buffer pool | Ratios de acierto de lectura y escritura, esperas de buffers, contadores de lectura/escritura y foreground writes | El acierto de lectura avisa por debajo de `95%` y es crítico por debajo de `90%` |
| Locks y concurrencia | Esperas de lock, deadlocks, timeouts, desbordamientos y locks retenidos | Los deadlocks y desbordamientos son críticos a `1` |
| Sesiones | Sesiones activas | Gauge |
| Checkpoints | Número y esperas de checkpoints, duración, tiempo de bloqueo, buffers sucios y última razón/tipo | La última razón y el tipo son módulos de texto |
| Consultas y recursos | Sequential scans, sorts y disk sorts | Contadores incrementales |
| Tablas activas | Top-N tablas por lecturas: lecturas, lecturas de disco, escrituras, escrituras de disco y sequential scans | Solo con **Top active tables** activo |
| I/O por dbspace | Operaciones y páginas de lectura/escritura de cada dbspace | Solo con **Per-dbspace I/O** activo |

Los contadores que crecen desde el arranque del servidor (`sysprofile`, `sysptprof`, `sysvpprof`, I/O) se emiten como módulos **incrementales**. Los porcentajes, duraciones, recuentos de sesiones y estados se emiten como gauges o texto. Pandora FMS calcula la tasa a partir de los contadores incrementales y trata un reinicio del contador como un reinicio.

### Vista de consola

La vista IBM Informix agrupa los módulos por agente, muestra una tabla resumen de dbspaces y una tabla por familia de métricas. También incluye una sección de analítica con cinco gráficas:

- una gráfica de tarta con la distribución de los módulos visibles por estado;
- barras horizontales con el mayor uso de cada dbspace entre las instancias visibles;
- barras horizontales con las tablas activas con más lecturas;
- barras horizontales con el número de módulos visibles por familia de métricas;
- una gráfica de líneas con puntos que muestra la evolución del uso de los dbspaces para el periodo seleccionado.

![Vista IBM Informix con las tarjetas de resumen y las gráficas de analítica.](../assets/images/discovery/informix/dashboard.png)

Las barras de uso de dbspace usan los mismos umbrales de aviso y crítico que los módulos, y la línea de evolución usa el periodo seleccionado en el filtro lateral.

Las tablas de detalle agrupan los módulos por familia de métricas:

![Tablas de detalle de IBM Informix agrupadas por familia de métricas.](../assets/images/discovery/informix/dashboard-modules.png)

El filtro lateral usa el menú de filtros estándar de la consola:

![Filtro lateral con los filtros de agente, categoría, dbspace, nombre de módulo, estado y periodo de evolución.](../assets/images/discovery/informix/dashboard-filters.png)

- **Agents**: limita la vista a las instancias seleccionadas.
- **Metric categories**: muestra solo las familias seleccionadas.
- **Dbspaces**: muestra solo los módulos cuyo marcador de dbspace en `extra_data` coincide.
- **Module name**: búsqueda de texto sobre el nombre y la descripción del módulo.
- **Status**: muestra solo módulos Normal, Warning, Critical o Unknown.
- **Evolution period**: ventana de histórico que usa la gráfica de evolución del uso de dbspaces.

Si desmarca el interruptor **All** de agentes o de categorías de métricas, la vista pide seleccionar al menos un agente y una categoría de métricas en lugar de mostrar gráficas vacías.

La vista identifica agentes y módulos a través de `extra_data`; no depende de nombres traducidos, alias ni patrones de nombre de módulo.

## Solución de problemas

| Síntoma | Causa probable | Comprobación |
|---------|----------------|--------------|
| `Connection status` vale `0` en todos los objetivos | Red, host o puerto incorrectos, o la instancia no escucha | Pruebe el puerto TCP desde el servidor de Discovery y revise el formato del objetivo |
| `IfxPy is not installed` en la información de la tarea | Falta la dependencia Python en el servidor de Discovery | Ejecute el `setup.sh` del addon y compruebe el entorno virtual que usa la tarea |
| La conexión falla después de instalar el driver | El runtime del Client SDK no está disponible para el proceso del plugin | Instale el IBM Informix Client SDK y exporte `INFORMIXDIR` |
| Error de permisos al leer una familia | El usuario no tiene `SELECT` sobre la vista SMI | Conceda `SELECT` sobre la vista o desactive esa familia |
| `Maximum execution time reached` | El presupuesto de la tarea es pequeño para el número de instancias o la latencia | Aumente **Max execution time** o divida la tarea |
| Una familia está vacía pero la instancia está levantada | Esa familia está desactivada o el usuario no puede leer sus vistas | Active la familia y revise la información de la tarea |
| La vista de consola no muestra agentes | No ha corrido ninguna tarea o los agentes están deshabilitados | Ejecute la tarea una vez y compruebe que `tagente.extra_data` empieza por `informix:agent:` |
| La vista de consola no muestra módulos para un filtro | Los filtros excluyen todos los módulos | Limpie los filtros de agentes, categorías, dbspace, nombre y estado |

## Referencia

### Parámetros de la tarea

| Clave INI | Argumento CLI | Por defecto | Descripción |
|-----------|---------------|-------------|-------------|
| `credentials` | `--credentials` | — | Carga útil de credenciales en base64 del almacén de credenciales de Pandora FMS |
| `user` | `--user` | — | Alternativa manual para el usuario de Informix |
| `password` | `--password` | — | Alternativa manual para la contraseña de Informix |
| `connection_timeout` | `--connection_timeout` | `20` | Timeout de conexión en segundos |
| `query_timeout` | `--query_timeout` | `120` | Timeout de cada consulta SQL en segundos |
| `max_execution_time` | `--max_execution_time` | `240` | Presupuesto de la ejecución completa en segundos; `0` lo desactiva |
| `monitor_engine` | `--monitor_engine` | `true` | Estado del motor, versión, uptime y virtual processors |
| `monitor_storage` | `--monitor_storage` | `true` | Dbspaces, chunks y logical logs |
| `monitor_buffers` | `--monitor_buffers` | `true` | Ratios y contadores del buffer pool |
| `monitor_locks` | `--monitor_locks` | `true` | Locks, deadlocks, timeouts y desbordamientos |
| `monitor_checkpoints` | `--monitor_checkpoints` | `true` | Métricas y esperas de checkpoint |
| `monitor_queries` | `--monitor_queries` | `true` | Sequential scans, sorts y tablas activas |
| `monitor_sessions` | `--monitor_sessions` | `true` | Sesiones activas |
| `monitor_tables` | `--monitor_tables` | `true` | Top-N tablas desde `sysptprof` |
| `monitor_io` | `--monitor_io` | `false` | I/O por dbspace desde `syschkio` |
| `top_tables` | `--top_tables` | `10` | Número de tablas activas a monitorizar, `1`–`100` |
| `agent_prefix` | `--agent_prefix` | — | Prefijo añadido al alias del agente |
| `module_prefix` | `--module_prefix` | — | Prefijo añadido a cada nombre de módulo |
| `allow_list` | `--allow_list` | — | Lista de permitidos regex para nombres de módulo |
| `deny_list` | `--deny_list` | — | Lista de denegados regex para nombres de módulo |
| `transfer_mode` | `--transfer_mode` | `native` | `native` o `tentacle` |
| `tentacle_ip` | `--tentacle_ip` | `127.0.0.1` | Dirección de Tentacle |
| `tentacle_port` | `--tentacle_port` | `41121` | Puerto de Tentacle |
| `agents_group` | `--agents_group` | — | Nombre de grupo usado en modo Tentacle |
| `agents_group_id` | `--agents_group_id` | — | Identificador de grupo usado en modo nativo |
| `interval` | `--interval` | `300` | Intervalo del agente en segundos |

### Inventario de módulos

La siguiente tabla lista todas las familias de módulos que puede generar el addon. `N` es el nombre del dbspace y `DB.TABLE` es el nombre de la base de datos y la tabla.

| Categoría | Módulo | Tipo | Umbrales por defecto | `extra_data` |
|-----------|--------|------|----------------------|--------------|
| Motor | Connection status | `generic_proc` | — | `informix:engine:connection` |
| Motor | Informix engine status | `generic_proc` | — | `informix:engine:status` |
| Motor | Informix server mode | `generic_data_string` | — | `informix:engine:mode` |
| Motor | Informix version | `generic_data_string` | — | `informix:engine:version` |
| Motor | Informix uptime | `generic_data` | — | `informix:engine:uptime` |
| Motor | Informix host name | `generic_data_string` | — | `informix:engine:hostname` |
| Motor | Virtual processors | `generic_data` | — | `informix:engine:vp_count` |
| Motor | Virtual processor user CPU | `generic_data_inc` | — | `informix:engine:vp_usercpu` |
| Motor | Virtual processor system CPU | `generic_data_inc` | — | `informix:engine:vp_syscpu` |
| Dbspace | Dbspace `N` usage % | `generic_data` | Warning `80`, crítico `90` | `informix:dbspace:N` |
| Dbspace | Dbspace `N` free MB | `generic_data` | — | `informix:dbspace:N` |
| Dbspace | Dbspace `N` used MB | `generic_data` | — | `informix:dbspace:N` |
| Dbspace | Dbspace `N` total MB | `generic_data` | — | `informix:dbspace:N` |
| Dbspace | Dbspace `N` chunks | `generic_data` | — | `informix:dbspace:N` |
| Almacenamiento | Chunks offline | `generic_data` | Crítico `1` | `informix:storage:chunks_offline` |
| Almacenamiento | Chunks inconsistent | `generic_data` | Crítico `1` | `informix:storage:chunks_inconsistent` |
| Almacenamiento | Logical logs free | `generic_data` | Warning por debajo de `3`, crítico `0` | `informix:storage:logs_free` |
| Almacenamiento | Logical logs not backed up | `generic_data` | Crítico `1` | `informix:storage:logs_not_backed_up` |
| Almacenamiento | Logical logs used % | `generic_data` | — | `informix:storage:logs_used_pct` |
| Almacenamiento | Logical logs current | `generic_data` | — | `informix:storage:logs_current` |
| Buffers | Buffer read hit ratio % | `generic_data` | Warning por debajo de `95`, crítico por debajo de `90` | `informix:buffers:read_hit` |
| Buffers | Buffer write hit ratio % | `generic_data` | Warning por debajo de `95`, crítico por debajo de `90` | `informix:buffers:write_hit` |
| Buffers | Buffer waits | `generic_data_inc` | — | `informix:buffers:waits` |
| Buffers | Buffer reads | `generic_data_inc` | — | `informix:buffers:bufreads` |
| Buffers | Disk reads | `generic_data_inc` | — | `informix:buffers:dskreads` |
| Buffers | Page reads | `generic_data_inc` | — | `informix:buffers:pagreads` |
| Buffers | Buffer writes | `generic_data_inc` | — | `informix:buffers:bufwrites` |
| Buffers | Disk writes | `generic_data_inc` | — | `informix:buffers:dskwrites` |
| Buffers | Page writes | `generic_data_inc` | — | `informix:buffers:pagwrites` |
| Buffers | Foreground writes | `generic_data_inc` | Warning `1` | `informix:buffers:fgwrites` |
| Locks | Lock waits | `generic_data_inc` | — | `informix:locks:lockwts` |
| Locks | Deadlocks | `generic_data_inc` | Crítico `1` | `informix:locks:deadlks` |
| Locks | Lock timeouts | `generic_data_inc` | — | `informix:locks:lktouts` |
| Locks | Lock table overflows | `generic_data_inc` | Crítico `1` | `informix:locks:ovlock` |
| Locks | Transaction overflows | `generic_data_inc` | Crítico `1` | `informix:locks:ovtrans` |
| Locks | User thread overflows | `generic_data_inc` | Crítico `1` | `informix:locks:ovuserthread` |
| Locks | Locks held | `generic_data` | — | `informix:locks:held` |
| Sesiones | Active sessions | `generic_data` | — | `informix:sessions:active` |
| Checkpoints | Checkpoint waits | `generic_data_inc` | — | `informix:checkpoints:waits` |
| Checkpoints | Checkpoint count | `generic_data_inc` | — | `informix:checkpoints:count` |
| Checkpoints | Last checkpoint duration | `generic_data` | — | `informix:checkpoints:duration` |
| Checkpoints | Last checkpoint blocking time | `generic_data` | — | `informix:checkpoints:blocking_time` |
| Checkpoints | Last checkpoint critical waits | `generic_data` | — | `informix:checkpoints:critical_waits` |
| Checkpoints | Last checkpoint dirty buffers | `generic_data` | — | `informix:checkpoints:dirty_buffers` |
| Checkpoints | Last checkpoint physical log used | `generic_data` | — | `informix:checkpoints:physused` |
| Checkpoints | Last checkpoint logical log used | `generic_data` | — | `informix:checkpoints:logused` |
| Checkpoints | Last checkpoint reason | `generic_data_string` | — | `informix:checkpoints:reason` |
| Checkpoints | Last checkpoint type | `generic_data_string` | — | `informix:checkpoints:type` |
| Consultas | Sequential scans | `generic_data_inc` | — | `informix:queries:seqscans` |
| Consultas | Sorts | `generic_data_inc` | — | `informix:queries:totalsorts` |
| Consultas | Disk sorts | `generic_data_inc` | — | `informix:queries:dsksorts` |
| Tablas | Table `DB.TABLE` reads | `generic_data_inc` | — | `informix:tables:DB.TABLE` |
| Tablas | Table `DB.TABLE` disk reads | `generic_data_inc` | — | `informix:tables:DB.TABLE` |
| Tablas | Table `DB.TABLE` writes | `generic_data_inc` | — | `informix:tables:DB.TABLE` |
| Tablas | Table `DB.TABLE` disk writes | `generic_data_inc` | — | `informix:tables:DB.TABLE` |
| Tablas | Table `DB.TABLE` sequential scans | `generic_data_inc` | — | `informix:tables:DB.TABLE` |
| I/O | Dbspace `N` I/O reads | `generic_data_inc` | — | `informix:io:N` |
| I/O | Dbspace `N` I/O writes | `generic_data_inc` | — | `informix:io:N` |
| I/O | Dbspace `N` pages read | `generic_data_inc` | — | `informix:io:N` |
| I/O | Dbspace `N` pages written | `generic_data_inc` | — | `informix:io:N` |

### Ejecución manual

```bash
./setup.sh
venv/bin/python pandora_informix.py \
  --conf /path/to/task.conf \
  --targets_file /path/to/targets.txt
```

El addon también acepta `--targets "host:port/server,host2/server2"` para una ejecución manual rápida y `--as_server_plugin true` para el código de resultado del plugin de servidor.
