# Microsoft SQL Server Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de Microsoft SQL Server se conecta a instancias y bases de datos de Microsoft SQL Server y convierte su estado y su rendimiento en agentes y módulos de Pandora FMS. Lee una lista de instancias objetivo, se conecta con un login de SQL Server y recoge métricas de nivel de instancia y de nivel de base de datos mediante vistas del sistema y contadores de rendimiento.

Una tarea de Discovery crea un agente por instancia objetivo por defecto, y un agente por base de datos cuando **Create agent per database** está habilitado. Cada agente lleva las métricas de instancia de su objetivo y las métricas de las bases de datos que monitoriza. Se pueden definir consultas personalizadas para añadir un módulo por consulta y objetivo.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.13` (`pandorafms.mssql`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| Una instancia de Microsoft SQL Server alcanzable | `Requerido` | El plugin establece conexiones remotas con cada instancia monitorizada. Prerrequisito, no una declaración de compatibilidad. |
| Un login de SQL Server con **VIEW SERVER STATE** | `Requerido` | Necesario para leer las vistas del sistema y las peticiones en ejecución de la instancia. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a SQL Server](#preparar-el-acceso-a-sql-server). |
| Un login de SQL Server con **SELECT** | `Requerido` | Necesario para ejecutar las consultas personalizadas sobre tablas y vistas. Prerrequisito, no una declaración de compatibilidad. |
| El controlador ODBC 17 para SQL Server de Microsoft y unixODBC | `Requerido` | Solo cuando **ODBC mode** está habilitado; el plugin se conecta mediante ese nombre de controlador ODBC. |
| Una versión concreta de Pandora FMS | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión de consola o de servidor. |
| Un sistema operativo concreto del host | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con sistemas operativos para la máquina que ejecuta el plugin. |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Conectividad** entre el servidor de Pandora FMS y cada instancia de Microsoft SQL Server (puerto por defecto `1433`).
3. **Un login de SQL Server** con los permisos necesarios. Consulte [Preparar el acceso a SQL Server](#preparar-el-acceso-a-sql-server).
4. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados, tomados de la tarea de Discovery.
5. **Para el modo ODBC**, el controlador ODBC 17 para SQL Server de Microsoft y unixODBC instalados en la máquina que ejecuta el plugin.

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) con sus dependencias de Python empaquetadas, por lo que no es necesario instalar librerías de Python adicionales en el servidor de Discovery.

### Preparar el acceso a SQL Server

El login usado por la tarea debe alcanzar cada instancia por red y disponer de los permisos que necesita el monitor. Según los prerrequisitos oficiales:

- **VIEW SERVER STATE** para ejecutar `SELECT @@VERSION`, para leer `sys.dm_os_sys_info` (tiempo de actividad del servidor), `sys.dm_exec_requests` (peticiones activas), `@@MAX_CONNECTIONS` (conexiones máximas permitidas) y para ejecutar `sp_who 'ACTIVE'` (sesiones activas).
- **SELECT** para ejecutar las consultas personalizadas sobre las tablas o vistas concretas a las que apuntan.

Conceda al login únicamente el acceso que exija su política de monitorización; el plugin solo lee y nunca modifica la configuración de SQL Server.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager** (la vista *Manage disco packages*). El paquete está disponible en la [librería de Pandora FMS](https://pandorafms.com/library/mssql-discovery/). Una vez cargado, **Microsoft SQL Server** aparece en la categoría **Applications** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Microsoft SQL Server**. El primer paso genérico define la tarea; el paquete añade **Microsoft SQL Server Base** y **Microsoft SQL Server Detailed**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El ID del grupo y el intervalo se pasan al plugin y se aplican a todos los agentes generados.

**Paso 2 — Microsoft SQL Server Base.** A qué conectarse y cómo:

- **Microsoft SQL Server target strings** es la lista de instancias a monitorizar, separadas por comas o una por línea. Cada objetivo es `SERVER`, `SERVER:PORT`, `SERVER\INSTANCE` o `SERVER:PORT\INSTANCE`. Las líneas que empiezan por `#` son comentarios. Para monitorizar bases de datos concretas de una instancia, añada `|db1;db2`; para monitorizar todas menos un conjunto, añada `!` antes de la `|`. Consulte [Bases de datos objetivo](#bases-de-datos-objetivo).
- **User** y **Password** son el login de SQL Server usado para conectarse.
- **ODBC mode** se conecta mediante el controlador ODBC en lugar del controlador nativo `pymssql`.

![Paso Base de la tarea de Discovery de Microsoft SQL Server: target strings, User y Password.](../assets/images/discovery/mssql-discovery/base-step.png)

**Paso 3 — Microsoft SQL Server Detailed.** Ejecución, distribución de agentes y qué métricas se recogen:

- **Max threads** reparte los objetivos y las bases de datos entre varios trabajadores en paralelo.
- **Target agent** define los nombres de agente de los objetivos, separados por comas o una por línea, en la misma posición que la lista de objetivos; una entrada en blanco usa la cadena del objetivo como nombre de agente.
- **Custom module prefix** se antepone a todos los nombres de módulo generados.
- **Scan databases** enumera las bases de datos de cada instancia automáticamente.
- **Create agent per database** crea un agente por base de datos, con **Custom database agent prefix** para nombrarlos.
- **Enable entities file re-scan interval** y **Re-scan entities file interval** controlan cada cuánto se reconstruye la caché de bases de datos descubiertas.
- Los conmutadores **Database monitoring modules** e **Instance monitoring modules** seleccionan qué grupos de métricas se recogen.
- **Rename default modules** y **Modules names** permiten reemplazar las etiquetas por defecto de los módulos, y **Execute custom queries** y **Custom queries** definen las consultas personalizadas.

![Paso Detailed de la tarea de Discovery de Microsoft SQL Server: campos de ejecución y distribución de agentes.](../assets/images/discovery/mssql-discovery/detailed-top.png)

![Paso Detailed de la tarea de Discovery de Microsoft SQL Server: renombrado de módulos y consultas personalizadas.](../assets/images/discovery/mssql-discovery/detailed-mid.png)

![Paso Detailed de la tarea de Discovery de Microsoft SQL Server: conmutadores de monitorización de base de datos e instancia.](../assets/images/discovery/mssql-discovery/detailed-modules.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de **Total agents**, **Targets up** y **Targets down**. Con **Create agent per database** habilitado, informa también de **Databases agents**. Targets up son las instancias a las que el plugin logró conectarse.

2. **Los agentes.** Aparece un agente por instancia objetivo alcanzable, con el nombre de la lista **Target agent** o la cadena del objetivo. Con **Create agent per database**, aparece un agente por base de datos descubierta o listada.

3. **Los módulos de instancia.** Una instancia alcanzable lleva sus métricas de motor, memoria, búfer, conexión, consulta y disponibilidad según los conmutadores habilitados.

4. **Los módulos de base de datos.** Cada base de datos monitorizada lleva sus métricas de estado, disponibilidad, transacciones, registro, copia de seguridad, grupos de archivos y espacio de tablas según los conmutadores habilitados, y los módulos de consultas personalizadas.

Los objetivos a los que no se puede llegar se cuentan en **Targets down** y no generan agentes.

![Resumen de ejecución de una tarea de Discovery de Microsoft SQL Server.](../assets/images/discovery/mssql-discovery/task-summary.png)

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por instancia objetivo por defecto. El nombre del agente es el valor de la lista **Target agent** que coincide con la posición del objetivo, o la propia cadena del objetivo cuando no se indica ninguno. Cada agente generado informa de `MSSQL` como sistema operativo, su `os_version` es la versión de SQL Server devuelta por `SELECT @@VERSION` (o `Discovery` cuando no se puede leer), su `address` es el host de la instancia, y pertenece al grupo de la tarea (por ID) con el intervalo de la tarea.

Con **Create agent per database**, el plugin crea además un agente por base de datos, llamado `<Custom database agent prefix><instancia> <base de datos>`, y los cuenta en **Databases agents**. Los módulos de base de datos se colocan entonces en esos agentes.

Las bases de datos a monitorizar se listan explícitamente tras `|` en la cadena objetivo, o se descubren mediante el escaneo cuando **Scan databases** está habilitado. La lista de bases de datos descubiertas se guarda en el archivo de entidades, y **Enable entities file re-scan interval** decide cuándo se reconstruye ese archivo para incorporar bases de datos nuevas y descartar las eliminadas. Las bases de datos listadas explícitamente se monitorizan siempre.

### Módulos por agente

| Agente | Se crea cuando | Módulos que lleva |
| --- | --- | --- |
| Agente de instancia | Una instancia objetivo es alcanzable y no hay **Create agent per database** para sus bases de datos | Las métricas de instancia del objetivo, más las métricas de las bases de datos que monitoriza |
| Agente de base de datos | **Create agent per database** habilitado y una base de datos monitorizada | Las métricas de esa base de datos, más sus módulos de consultas personalizadas |

Los nombres de módulo son `<Custom module prefix>`, el nombre de la base de datos cuando el módulo es por base de datos, y el nombre del módulo. El inventario exhaustivo de módulos y el conmutador que habilita cada grupo están en [Módulos y agentes generados](#modulos-y-agentes-generados).

## Operación

### Ejecución manual

El plugin puede ejecutarse fuera de Discovery, desde un agente de Pandora FMS o directamente desde la línea de comandos, con un archivo de configuración y los archivos de objetivos, agentes y consultas personalizadas creados manualmente:

```bash
./pandora_mssql --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
```

Solo `--conf` y `--target_databases` son obligatorios; `--target_agents` y `--custom_queries` son opcionales. El plugin se conecta a cada objetivo en paralelo según **Max threads** y produce los agentes y módulos en su salida JSON de Discovery.

El archivo de configuración y las listas de objetivos contienen la contraseña de SQL Server en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalos fuera de directorios compartidos, registros y control de versiones. Seguir el flujo de Discovery para las ejecuciones de tarea significa que la consola construye estos archivos por usted.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente y el objetivo se informa como **Targets down** | Confirme que la instancia es alcanzable desde el servidor de Pandora FMS por su puerto (por defecto `1433`), que el servicio de SQL Server está en marcha y que **User** y **Password** son correctos. |
| Faltan módulos de instancia y la información de ejecución registra avisos de recuperación | El login necesita **VIEW SERVER STATE** para las vistas del sistema y los contadores de rendimiento de la instancia. Conceda ese permiso. |
| Faltan módulos de consultas personalizadas | La consulta debe estar entre `check_begin` y `check_end`, usar una sentencia `SELECT`, y el login necesita **SELECT** sobre las tablas o vistas referenciadas. Compruebe la expresión crontab si la consulta está programada. |
| Una base de datos no se monitoriza | Lístela tras `|` en la cadena objetivo o habilite **Scan databases**. La lista de bases de datos descubiertas se guarda en caché y se refresca solo tras **Re-scan entities file interval**. |
| No se crean agentes de base de datos | Habilite **Create agent per database**. Sin ello, los módulos de base de datos se colocan en el agente de instancia. |
| El modo ODBC no conecta | Instale el controlador ODBC 17 para SQL Server de Microsoft y unixODBC en la máquina que ejecuta el plugin. La conexión usa ese nombre de controlador. |
| Una consulta personalizada es rechazada | Solo se permiten sentencias `SELECT`; el resto se elimina y se informa en la información de ejecución. |
| Faltan módulos esperados | Revise los conmutadores **Database monitoring modules** e **Instance monitoring modules**: un grupo deshabilitado no produce módulos. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en dos pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Microsoft SQL Server Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Microsoft SQL Server target strings | `_dbstrings_` | textarea | — | Lista de instancias objetivo. Obligatorio |
| User | `_dbuser_` | string | — | Login de SQL Server. Obligatorio |
| Password | `_dbpass_` | password | — | Contraseña de SQL Server. Obligatorio |
| ODBC mode | `_odbcMode_` | checkbox | off | Se conecta mediante el controlador ODBC en lugar del controlador nativo |

#### Microsoft SQL Server Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `1` | Trabajadores que reparten los objetivos y las bases de datos |
| Target agent | `_engineAgent_` | string | — | Nombres de agente de los objetivos, en la posición de la lista; en blanco usa la cadena del objetivo |
| Custom module prefix | `_prefixModuleName_` | string | — | Prefijo antepuesto a todos los nombres de módulo |
| Scan databases | `_scanDatabases_` | checkbox | off | Enumera las bases de datos de cada instancia |
| Create agent per database | `_agentPerDatabase_` | checkbox | off | Crea un agente por base de datos |
| Custom database agent prefix | `_prefixAgent_` | string | — | Prefijo de los agentes de base de datos. Solo se muestra cuando **Create agent per database** está habilitado |
| Enable entities file re-scan interval | `_enableEntitiesInterval_` | checkbox | off | Reconstruye la caché de bases de datos descubiertas tras el intervalo |
| Re-scan entities file interval | `_entitiesInterval_` | select | `86400` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Retrieve logs statistics | `_checkLogs_` | checkbox | on | Módulos de registro por base de datos: flush, crecimiento, reducción, tamaño, uso y caché |
| Monitor active users | `_monitorUsers_` | checkbox | on | Transacciones de usuarios activos por base de datos |
| Retrieve transactions statistics | `_checkTransactions_` | checkbox | on | Transacciones y transacciones activas por base de datos |
| Monitor filegroups space | `_checkFilegroups_` | checkbox | on | Espacio libre por grupo de archivos |
| Monitor user reserved space | `_checkUserSpace_` | checkbox | on | Espacio reservado por tabla de usuario |
| Monitor backups | `_checkBackups_` | checkbox | on | Tiempo desde y fecha de la última copia de seguridad |
| Check engine uptime | `_checkUptime_` | checkbox | on | Detección de reinicio del servidor |
| Retrieve query statistics | `_queryStats_` | checkbox | off | Número de consultas `SELECT`, `INSERT`, `DELETE` y `UPDATE` en ejecución |
| Analyze connections | `_checkConnections_` | checkbox | on | Uso de sesiones frente a las conexiones máximas |
| Monitor long queries | `_checkLongQueries_` | checkbox | on | Consultas de ejecución larga y su salida |
| Monitor latch requests | `_checkLatchRequests_` | checkbox | on | Peticiones de serialización de latch |
| Monitor full scans | `_checkFullScans_` | checkbox | on | Escaneos completos de tablas o índices |
| Count databases | `_checkDatabasesCount_` | checkbox | on | Número de bases de datos existentes |
| Retrieve memory statistics | `_checkMemory_` | checkbox | on | Memoria de bloqueo, conexión, optimizador, caché SQL y total del servidor |
| Retrieve locks statistics | `_checkLocks_` | checkbox | on | Interbloqueos, timeouts de bloqueo, peticiones de bloqueo y esperas de bloqueo |
| Check engine performance | `_checkEnginePerformance_` | checkbox | on | Porcentaje de CPU y de E/S ocupados de la instancia |
| Retrieve buffer statistics | `_checkBuffer_` | checkbox | on | Ratio de acierto de caché de búfer y conexiones libres |
| Retrieve users information | `_checkUsersInformation_` | checkbox | on | Usuarios activos, bloqueados y en espera, y el ratio de conexión |
| Retrieve Cluster State | `_checkClusterState_` | checkbox | off | Estados del grupo de disponibilidad AlwaysOn y de las réplicas |
| Rename default modules | `_renameModules_` | checkbox | on | Reemplaza las etiquetas por defecto de los módulos |
| Modules names | `_ModulesNames_` | textarea | — | Bloque `[MODULE_NAMES]` que renombra los módulos por defecto. Solo se muestra cuando **Rename default modules** está habilitado |
| Execute custom queries | `_executeCustomQueries_` | checkbox | on | Habilita las consultas personalizadas |
| Custom queries | `_customQueries_` | textarea | — | Definición de las consultas personalizadas. Solo se muestra cuando **Execute custom queries** está habilitado |

### Archivo de configuración

La tarea de Discovery construye un archivo `--conf` temporal a partir de sus propios campos. Una ejecución manual lo suministra directamente. El archivo tiene una sección `[CONF]` y una sección opcional `[MODULE_NAMES]`.

Preferencias de motor y monitorización:

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `agents_group_id` | `10` | ID del grupo donde se crean los agentes |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes |
| `user` | Vacío | Usuario de conexión. Obligatorio |
| `password` | Vacío | Contraseña del usuario. Obligatorio |
| `threads` | `1` | Número de trabajadores en paralelo |
| `modules_prefix` | Vacío | Prefijo de los nombres de módulo |
| `entities_list` | `/tmp/mssql_entities_list.txt` | Archivo que guarda en caché las bases de datos descubiertas |
| `enable_entities_interval` | `1` | Reconstruye la caché de bases de datos tras el intervalo |
| `entities_interval` | `300` | Segundos antes de reconstruir la caché de bases de datos |
| `scan_databases` | `0` | Enumera las bases de datos de cada instancia |
| `odbc_mode` | `0` | Se conecta mediante el controlador ODBC |
| `agent_per_database` | `0` | Crea un agente por base de datos |
| `db_agent_prefix` | Vacío | Prefijo de los nombres de los agentes de base de datos |
| `rename_modules` | `1` | Aplica las etiquetas de `[MODULE_NAMES]` |
| `execute_custom_queries` | `1` | Habilita las consultas personalizadas |

Conmutadores de monitorización (cada `1` habilita el grupo, cada `0` lo deshabilita):

| Clave | Por defecto | Habilita |
| --- | --- | --- |
| `engine_uptime` | `1` | Detección de reinicio |
| `query_stats` | `1` | Conteo de consultas `SELECT`/`INSERT`/`DELETE`/`UPDATE` |
| `analyze_connections` | `1` | Uso de sesiones |
| `count_databases` | `1` | Recuento de bases de datos |
| `retrieve_memory_statistics` | `1` | Estadísticas de memoria |
| `retrieve_locks_statistics` | `1` | Estadísticas de bloqueos |
| `retrieve_buffer_statistics` | `1` | Ratio de acierto de búfer y conexiones libres |
| `monitor_latch_requests` | `1` | Esperas de latch |
| `monitor_full_scans` | `1` | Escaneos completos |
| `check_engine_performance` | `1` | CPU y E/S del servidor |
| `retrieve_users_information` | `1` | Información de usuarios |
| `monitor_long_queries` | `1` | Consultas de ejecución larga |
| `retrieve_cluster_state` | `0` | Estado del clúster AlwaysOn |
| `retrieve_logs_statistics` | `1` | Estadísticas de registro |
| `monitor_active_users` | `1` | Transacciones de usuarios activos |
| `retrieve_transactions_statistics` | `1` | Transacciones |
| `monitor_filegroups_space` | `1` | Espacio de grupos de archivos |
| `monitor_user_reserved_space` | `1` | Espacio de tablas de usuario |
| `monitor_backups` | `1` | Copias de seguridad |

La sección `[MODULE_NAMES]` asocia cada clave de módulo por defecto con la etiqueta que aparece en la consola, por ejemplo `database_size = database_size` y `restart_detection = restart detection`. Solo se renombran los módulos de los grupos habilitados.

El archivo `--conf` y las listas de objetivos contienen la contraseña de SQL Server en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalos fuera de directorios compartidos, registros y control de versiones.

### Bases de datos objetivo

El archivo `--target_databases` contiene una o más cadenas objetivo, separadas por comas o una por línea. Las líneas que empiezan por `#` y las líneas en blanco se ignoran.

Cada objetivo sigue `SERVER`, `SERVER:PORT`, `SERVER\INSTANCE` o `SERVER:PORT\INSTANCE`. Para monitorizar bases de datos concretas de una instancia, añada `|` y separe las bases de datos con `;`:

```text
172.17.0.4:1433\DEVENV|pandora;testing;model
```

Para monitorizar todas las bases de datos excepto un conjunto, añada `!` antes de la `|`:

```text
172.17.0.4:1433\DEVENV!|pandora;testing;model
```

### Agentes objetivo

El archivo opcional `--target_agents` contiene un nombre de agente por objetivo, separados por comas o una por línea. La posición de cada nombre coincide con la posición del objetivo correspondiente en la lista de objetivos; las líneas en blanco se ignoran. Una entrada en blanco deja el agente con el nombre de la cadena del objetivo (su IP o FQDN).

```text
agente1,,agente3
agente4
agente5,agente6,agente7,,agente9
```

### Ejecución en línea de comandos

El plugin acepta un archivo de configuración, un archivo de bases de datos objetivo, un archivo opcional de agentes objetivo y un archivo opcional de consultas personalizadas:

```bash
./pandora_mssql --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta obligatoria al archivo de configuración |
| `--target_databases` | Ruta obligatoria al archivo con las instancias objetivo |
| `--target_agents` | Ruta opcional al archivo con los nombres de agente objetivo |
| `--custom_queries` | Ruta opcional al archivo con las consultas personalizadas |

Ejemplo de archivo de configuración:

```ini
[CONF]
agents_group_id=10
interval=300
user=<SQL_LOGIN>
password=<SQL_PASSWORD>
threads=1
modules_prefix=
execute_custom_queries=1
engine_uptime=1
query_stats=1
analyze_connections=1
count_databases=1
retrieve_memory_statistics=1
retrieve_locks_statistics=1
check_engine_performance=1
retrieve_buffer_statistics=1
retrieve_users_information=1
monitor_long_queries=1
monitor_latch_requests=1
monitor_full_scans=1
retrieve_logs_statistics=1
monitor_active_users=1
retrieve_transactions_statistics=1
monitor_filegroups_space=1
monitor_user_reserved_space=1
monitor_backups=1
agent_per_database=0
scan_databases=1

[MODULE_NAMES]
database_size=database_size
database_usage=database_usage
restart_detection=restart detection
```

### Consultas personalizadas

Cada consulta personalizada crea un módulo por agente de tarea y se define entre `check_begin` y `check_end`:

| Campo | Descripción |
| --- | --- |
| `name` | Nombre del módulo |
| `description` | Descripción del módulo |
| `operation` | `value` devuelve un único valor, `full` devuelve todas las filas como cadena |
| `datatype` | `generic_data`, `generic_data_string` o `generic_proc` |
| `min_warning`, `max_warning` | Umbrales numéricos de aviso |
| `str_warning` | Condición de aviso como cadena |
| `warning_inverse` | `1` invierte el intervalo de umbral de aviso |
| `min_critical`, `max_critical` | Umbrales numéricos de crítico |
| `str_critical` | Condición de crítico como cadena |
| `critical_inverse` | `1` invierte el intervalo de umbral crítico |
| `module_interval` | Intervalo del módulo, como multiplicador del intervalo del agente |
| `crontab` | Expresión cron de 5 campos; la consulta solo se ejecuta cuando la fecha/hora coincide. Vacío se ejecuta en cada intervalo |
| `target` | La consulta, solo `SELECT` |
| `target_databases` | Objetivos o bases de datos donde se crea el módulo; `all` o vacío aplica a todos |
| `target_scope` | `instances`, `databases` o `all`; vacío aplica a ambos |
| `ignore_databases` | Objetivos o bases de datos donde no se crea el módulo |

El campo `crontab` sigue el formato estándar de 5 campos (`minuto hora día_del_mes mes día_de_la_semana`) y admite `*`, valores exactos, rangos, pasos y listas. En la primera ejecución tras habilitar una consulta programada solo se recoge una ocurrencia dentro del intervalo actual, de modo que una consulta diaria o mensual no se ejecuta de inmediato.

```text
check_begin
name Select 1
description Number of invalid objects
operation value
datatype generic_data
min_warning 5
target SELECT 1;
target_databases all
check_end
```

### Módulos y agentes generados

Los nombres de módulo son `[<Custom module prefix>][<nombre de base de datos> ]<nombre de módulo>`. Las etiquetas siguientes son los valores por defecto de `[MODULE_NAMES]`; con **Rename default modules** habilitado se pueden reemplazar.

**Métricas de instancia (en el agente de instancia)**

Siempre se crean:

- `database_size`: `generic_data`, el tamaño de la base de datos; MB.
- `database_usage`: `generic_data`, porcentaje de la base de datos utilizado; unidad `%`.
- `server_startup`: `generic_data`, tiempo de actividad del servidor de base de datos en días.
- `page_reads`: `generic_data_inc`, lecturas de página de base de datos por segundo.
- `page_writes`: `generic_data_inc`, escrituras de página de base de datos por segundo.
- `locks_used`: `generic_data`, bloques de bloqueo y de propietario usados; unidad `%`.
- `workspace_memory`: `generic_data`, memoria de espacio de trabajo concedida; unidad `%`.
- `average_waittime`: `generic_data`, tiempo medio de espera de bloqueo; unidad `ms`.

Se crean cuando el conmutador correspondiente está habilitado:

- **Check engine uptime**: `restart detection` (`generic_proc`, `0` cuando se detecta un reinicio, `1` en caso contrario).
- **Retrieve query statistics**: `queries`, `insert`, `delete`, `update` (`generic_data`, recuento de consultas en ejecución por tipo, dentro del intervalo).
- **Analyze connections**: `session usage` (`generic_data`, sesiones actuales como porcentaje del máximo; unidad `%`).
- **Count databases**: `database_count` (`generic_data`, número de bases de datos existentes).
- **Retrieve memory statistics**: `lock_memory`, `connection_memory`, `optimizer_memory`, `sqlcache_memory`, `total_memory` (`generic_data`, bytes).
- **Retrieve locks statistics**: `deadlocks` (`generic_data`, interbloqueos por segundo), `lock_timeouts`, `lock_requests`, `lock_waits` (`generic_data_inc`). `lock_waits` lleva un umbral crítico en `90`.
- **Retrieve buffer statistics**: `buf_cachehit_ratio` (`generic_data`, páginas encontradas en la caché de búfer; unidad `%`), `free_connections` (`generic_data`, conexiones libres; unidad `%`).
- **Monitor latch requests**: `latch_waits` (`generic_data_inc`, peticiones de latch por segundo).
- **Monitor full scans**: `full_scans` (`generic_data_inc`, escaneos completos por segundo).
- **Check engine performance**: `server_cpu` (`generic_data`, uso de CPU de la instancia; unidad `%`, crítico en `90`), `server_io` (`generic_data_inc`, E/S ocupada; unidad `%`, crítico en `80`).
- **Retrieve users information**: `active_connection_ratio` (`generic_data_string`, conexiones activas frente al total; unidad `%`), `locked_users`, `blocked_users`, `active_users` (`generic_data`).
- **Monitor long queries**: `long_queries` (`generic_data`, segundos de la consulta en ejecución más larga; unidad `s`, crítico en `600`), `long_queries_string` (`async_string`, la salida de las consultas de ejecución larga).
- **Retrieve Cluster State**: `aag_cluster_quorum_state`, `aag_cluster_members_state <miembro>`, `aag_synchronization_health`, `aag_replica_synchronization_health <réplica>`, `aag_replica_connected_state <réplica>`, `aag_replica_recovery_health`, `aag_replica_operational_state`, `aag_db_replica_synchronization_state <base de datos>` (`generic_proc`), `aag_listener_state <réplica>` (`generic_data`, estados del grupo de disponibilidad AlwaysOn y de las réplicas, con umbrales críticos invertidos).

**Métricas de base de datos (en el agente de base de datos, o en el agente de instancia cuando **Create agent per database** está deshabilitado)**

Siempre se crean:

- `availability`: `generic_proc`, `1` cuando la base de datos existe.
- `state`: `generic_data`, el estado de la base de datos.

Se crean cuando el conmutador correspondiente está habilitado:

- **Monitor active users**: `active users` (`generic_data`, transacciones de usuarios activos para la base de datos).
- **Retrieve transactions statistics**: `transactions` (`generic_data_inc`, transacciones por segundo), `active transactions` (`generic_data`).
- **Retrieve logs statistics**: `log_flush_waits` (`generic_data_inc`), `log_file_growths` (`generic_data`, unidad `%`), `log_file_shrinks` (`generic_data`), `logfile_size` (`generic_data`, MB), `logfile_usage` (`generic_data`, espacio libre en los archivos de registro; unidad `%`, crítico en `15`), `log_cachehit_ratio` (`generic_data`, unidad `%`).
- **Monitor backups**: `backup_status_minutes` (`generic_data`, minutos desde la última copia de seguridad), `backup_status_last_backup` (`generic_data` o `generic_data_string`, fecha de la última copia de seguridad, o `NEVER`).
- **Monitor filegroups space**: `fg_free_space` (`generic_data`, espacio libre en los grupos de archivos; unidad `%`, crítico en `15`).
- **Monitor user reserved space**: un módulo `table_space <tabla>` por tabla (`generic_data`, KB) y uno `table_space <tabla> free %` (`generic_data`, unidad `%`).
- **Execute custom queries**: un módulo por consulta personalizada, con el tipo de datos y los umbrales definidos en la consulta.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.mssql` |
| Versión del plugin | `1.13` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |