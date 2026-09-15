# PostgreSQL Discovery

*Última actualización del artículo: 2026-09-14.*

## Qué monitoriza

El plugin de Discovery de PostgreSQL monitoriza instancias PostgreSQL y sus bases de datos ejecutando consultas SQL contra ellas y convirtiendo los resultados en módulos de monitorización de Pandora FMS. Recoge disponibilidad, uptime, actividad de consultas, uso de conexiones, caché de buffers, fragmentación, almacenamiento, actividad de conexiones y transacciones por base de datos, estadísticas de tablas y cualquier consulta SQL personalizada que defina el operador.

El plugin crea **un agente principal por cada destino**. Cuando se activa **Scan databases** descubre las bases de datos de la instancia y crea sus módulos en el agente principal o en **un agente por cada base de datos**.

El plugin está pensado para usarse a través del sistema **Discovery** de Pandora FMS. No genera ficheros XML de agente: devuelve los agentes y módulos descubiertos en la salida JSON de la ejecución, y la tarea de Discovery los crea.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Versión del plugin `1.6` (`pandorafms.postgresql`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Descubrimiento de agentes de instancia y de base de datos con métricas por base de datos | `Probado` | Ejecución de verificación: una tarea terminó con `Targets up 3` y `Total agents 3`, y se creó un agente de base de datos con sus módulos. Consulte [Verificar la primera ejecución](#verificar-la-primera-ejecucion) |
| Alcance de red desde el servidor de Discovery a cada base de datos de destino | `Requerido` | El plugin abre una conexión PostgreSQL remota por cada destino |
| Un rol de PostgreSQL que pueda conectarse a las instancias y bases de datos monitorizadas | `Requerido` | Prerrequisito. Consulte [Prerrequisitos](#prerrequisitos) |
| PostgreSQL 17 y posteriores, módulos de caché de buffers | `Sin validar` | La guía rápida oficial indica que los módulos `backend used buffer cache`, `checkpoints buffer cache` y `cleaned buffer cache` no están disponibles |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | No se ha registrado ningún sistema operativo de host |
| Versiones del servidor PostgreSQL | `Sin validar` | La compatibilidad se estableció contra las consultas SQL y el contrato de conexión, no contra una matriz de versiones |

### Prerrequisitos

1. **Conectividad de red** entre el servidor de Discovery y cada instancia PostgreSQL de destino.
2. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.
3. **Un rol de PostgreSQL** que pueda conectarse a las bases de datos monitorizadas. Los módulos leen `pg_stat_activity`, `pg_settings`, `pg_database`, `pg_class`, `pg_namespace`, `pg_tables`, `pg_indexes`, `pg_stat_user_tables`, `pg_stat_database` y `pg_stat_bgwriter`.
4. **Una credencial almacenada** con el usuario y la contraseña de ese rol. Consulte [Crear la credencial](#crear-la-credencial).

El plugin se distribuye como una aplicación de Discovery autocontenida: el paquete `.disco` incluye su propio ejecutable, por lo que no hay que instalar ningún runtime adicional para una ejecución normal.

### Crear la credencial

La tarea no pide un usuario y una contraseña en claro. Selecciona una credencial **Custom** del almacén de credenciales de Pandora FMS:

1. Vaya a **Management → Configuration → Credential store**.
2. Cree una credencial **Custom** con el usuario y la contraseña de PostgreSQL.
3. Selecciónela en el campo **PostgreSQL Credentials** de la tarea.

Almacenar la credencial en el almacén evita que la contraseña quede en la definición de la tarea y en el fichero de configuración generado.

### Instalar el plugin

Cargue el paquete `.disco` de `pandorafms.postgresql` desde el marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/entries/pandorafms.postgresql](https://marketplace.pandorafms.com/entries/pandorafms.postgresql)

Una vez cargado, la aplicación **PostgreSQL** queda disponible al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → PostgreSQL**. La consola presenta los campos en dos pasos: **PostgreSQL Base** y **PostgreSQL Detailed**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **PostgreSQL Base** — los destinos y cómo alcanzarlos:

    - **PostgreSQL target strings**: uno o varios destinos, separados por comas o uno por línea. Cada entrada crea un agente principal. Consulte [Cadenas de destino](#cadenas-de-destino).
    - **PostgreSQL Credentials**: una credencial **Custom** del almacén de credenciales.

    ![Paso PostgreSQL Base de la tarea de Discovery, con el área de texto de cadenas de destino y el selector de credenciales](../assets/images/discovery/postgresql/postgresql-task-base.png)

2. **PostgreSQL Detailed** — alcance del descubrimiento y grupos de monitorización:

    - **Max threads**: número de conexiones concurrentes usadas para monitorizar los destinos.
    - **Target agent**: nombres que se asignan a los agentes principales, emparejados por posición con las cadenas de destino. Si se deja vacío, se usa la dirección del destino como nombre del agente.
    - **Custom module prefix**: se antepone a todos los nombres de módulo generados.
    - **Autodisabled agents**: crea los agentes generados en modo Autodisabled.
    - **Scan databases**: descubre las bases de datos de cada instancia.
    - **Create agent per database**: crea un agente por cada base de datos descubierta en lugar de añadir sus módulos al agente principal.
    - **Custom database agent prefix**: visible cuando **Create agent per database** está activado. Se antepone a los nombres de los agentes por base de datos.
    - **Enable entities file re-scan interval** y **Re-scan entities file interval**: persisten las bases de datos descubiertas y revalidan la lista periódicamente.
    - **Check engine uptime**, **Retrieve query statistics**, **Analyze connections**, **Calculate fragmentation ratio**, **Retrieve cache statistics**: grupos de módulos de instancia.
    - **Storage statistics**, **Query performance**, **Connections statistics**, **Transaction statistics**, **Table statistics**, **Advanced performance**: grupos de módulos por base de datos.
    - **Execute custom queries** y **Custom queries**: ejecutan SQL definido por el operador y crean un módulo por consulta.

    ![Paso PostgreSQL Detailed de la tarea de Discovery, con max threads, target agent, el prefijo de módulos, las casillas de descubrimiento y grupos de módulos, y el área de consultas personalizadas](../assets/images/discovery/postgresql/postgresql-task-detailed.png)

El nombre, el grupo, el intervalo y el timeout propios de la tarea se definen en el paso genérico de la tarea, que precede a estos dos. El grupo y el intervalo se convierten en el grupo de agentes y el intervalo de módulos.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea PostgreSQL completada informa de:

    - **Total agents**: número de agentes generados por la tarea.
    - **Targets up**: destinos a los que el plugin se pudo conectar.
    - **Targets down**: destinos a los que no pudo conectarse.

    ![Resumen de una tarea PostgreSQL completada, con Targets up 3, Targets down 0 y Total agents 3](../assets/images/discovery/postgresql/postgresql-task-summary.png)

2. **Los agentes.** Un agente principal por cada cadena de destino. Con **Scan databases** activado, las bases de datos descubiertas se añaden al agente principal o, con **Create agent per database**, se crean como agentes independientes.

3. **Los módulos de cada agente.** El agente principal siempre tiene `POSTGRESQL connection`. Una base de datos monitorizada produce al menos su módulo `connection`. El resto de módulos depende de las casillas activadas.

    ![Lista de módulos de un agente de base de datos PostgreSQL, con los módulos de conexión, almacenamiento, rendimiento de consultas, conexiones, transacciones, tablas y rendimiento avanzado](../assets/images/discovery/postgresql/postgresql-database-modules.png)

Si la tarea informa de `Targets down` para un destino, revise [Resolución de problemas](#resolucion-de-problemas).

## Entender los resultados

### Agentes y cardinalidad

- **Un agente principal por cada cadena de destino.** Su nombre es la dirección del destino salvo que se indique un nombre en **Target agent** para esa posición. El sistema operativo del agente se informa como `POSTGRESQL` y su versión de sistema operativo como la versión del servidor conectado.
- **Módulos de instancia** se crean siempre en el agente principal. El módulo `POSTGRESQL connection` está siempre presente y refleja si la conexión a la instancia se estableció.
- **Módulos de base de datos.** Con **Scan databases** activado, cada base de datos descubierta produce al menos un módulo `connection`.
    - Con **Create agent per database** desactivado, los módulos de la base de datos se añaden al agente principal y sus nombres llevan el nombre de la base de datos como prefijo, por ejemplo `<prefix><database> connection`.
    - Con **Create agent per database** activado, cada base de datos tiene su propio agente llamado `<database agent prefix><nombre del agente principal> <database>`, y los nombres de sus módulos no llevan el prefijo de la base de datos.

### Módulos de instancia

El módulo `POSTGRESQL connection` se crea siempre en el agente principal.

| Módulo | Tipo | Unidad | Se activa con |
|--------|------|--------|---------------|
| `<prefix>POSTGRESQL connection` | `generic_proc` | — | Siempre |
| `<prefix>restart detection` | `generic_proc` | — | Check engine uptime |
| `<prefix>queries` | `generic_data` | — | Retrieve query statistics |
| `<prefix>insert` | `generic_data` | — | Retrieve query statistics |
| `<prefix>delete` | `generic_data` | — | Retrieve query statistics |
| `<prefix>update` | `generic_data` | — | Retrieve query statistics |
| `<prefix>session usage` | `generic_data` | % | Analyze connections |
| `<prefix>allocated buffer cache` | `generic_data` | bytes | Retrieve cache statistics |
| `<prefix>backend used buffer cache` | `generic_data` | bytes | Retrieve cache statistics |
| `<prefix>checkpoints buffer cache` | `generic_data` | bytes | Retrieve cache statistics |
| `<prefix>cleaned buffer cache` | `generic_data` | bytes | Retrieve cache statistics |

Los módulos `queries`, `insert`, `delete` y `update` cuentan las sentencias que estuvieron activas durante el último intervalo. `restart detection` vale `0` cuando el motor se reinició en los dos últimos intervalos y `1` en caso contrario. `session usage` es el porcentaje de slots de conexión en uso frente al máximo configurado.

### Módulos de base de datos

Una base de datos monitorizada produce siempre su módulo **connection**, con valor `1` cuando la conexión se estableció y `0` cuando no. El resto de módulos depende de los grupos por base de datos activados.

| Módulo | Tipo | Unidad | Se activa con |
|--------|------|--------|---------------|
| `<prefix>connection` | `generic_proc` | — | Siempre (por base de datos descubierta) |
| `<prefix>fragmentation ratio` | `generic_data` | % | Calculate fragmentation ratio **y** Table statistics |
| `<prefix>database size` | `generic_data` | bytes | Storage statistics |
| `<prefix>tables size` | `generic_data` | bytes | Storage statistics |
| `<prefix>indexes size` | `generic_data` | bytes | Storage statistics |
| `<prefix>temp bytes` | `generic_data` | bytes | Storage statistics |
| `<prefix>temp files` | `generic_data` | — | Storage statistics |
| `<prefix>long queries` | `generic_data` | — | Query performance |
| `<prefix>oldest query age` | `generic_data` | seconds | Query performance |
| `<prefix>sequential scans` | `generic_data` | — | Query performance |
| `<prefix>index scans` | `generic_data` | — | Query performance |
| `<prefix>cache hit ratio` | `generic_data` | % | Query performance |
| `<prefix>active connections` | `generic_data` | — | Connections statistics |
| `<prefix>idle connections` | `generic_data` | — | Connections statistics |
| `<prefix>total connections` | `generic_data` | — | Connections statistics |
| `<prefix>transactions` | `generic_data` | — | Transaction statistics |
| `<prefix>commits` | `generic_data` | — | Transaction statistics |
| `<prefix>rollbacks` | `generic_data` | — | Transaction statistics |
| `<prefix>rollback ratio` | `generic_data` | % | Transaction statistics |
| `<prefix>deadlocks` | `generic_data` | — | Transaction statistics |
| `<prefix>conflicts` | `generic_data` | — | Transaction statistics |
| `<prefix>table count` | `generic_data` | — | Table statistics |
| `<prefix>index count` | `generic_data` | — | Table statistics |
| `<prefix>live tuples` | `generic_data` | — | Table statistics |
| `<prefix>dead tuples` | `generic_data` | — | Table statistics |
| `<prefix>blocks read` | `generic_data` | — | Advanced performance |
| `<prefix>blocks hit` | `generic_data` | — | Advanced performance |

Con **Create agent per database** desactivado, inserte el nombre de la base de datos después del prefijo personalizado: `<prefix><database> database size`. El módulo `fragmentation ratio` de base de datos requiere que **Calculate fragmentation ratio** y **Table statistics** estén ambos activados.

### Fichero de entidades y bases de datos desaparecidas

Con **Enable entities file re-scan interval** activado, el plugin persiste las bases de datos descubiertas en un fichero de entidades. Cuando una base de datos descubierta antes ya no aparece en el escaneo actual, el plugin sigue generando su módulo `connection`, de modo que el módulo puede pasar a estado crítico en lugar de desaparecer en silencio. Sin esta opción, la lista no se persiste y una base de datos que ya no se descubre deja de reportarse.

### Consultas personalizadas

Cada consulta personalizada genera un módulo en los agentes a los que aplica su ámbito. Una consulta puede dirigirse al nivel de instancia (`instances`), al nivel de base de datos (`databases`) o a ambos (`all`), puede limitarse a bases de datos concretas y puede programarse con una expresión crontab de cinco campos. Las consultas programadas conservan su última ejecución correcta, de modo que una ocurrencia perdida mientras el plugin no se ejecutaba se ejecuta en la siguiente ejecución de la tarea. Consulte [Referencia de consultas personalizadas](#referencia-de-consultas-personalizadas).

## Resolución de problemas

El plugin informa de sus diagnósticos en el resumen JSON de ejecución que imprime en la salida estándar: los errores de conexión se reportan como `Connection failed: ...`, y las consultas omitidas o fallidas se añaden ahí.

- **`Targets down` en un destino** — falló la conexión a la instancia. Compruebe el acceso de red desde el servidor de Discovery, el formato de la cadena de destino y la credencial seleccionada.
- **Una base de datos no se monitoriza** — no se descubrió. Active **Scan databases**, o lístela explícitamente en la cadena de destino con `\`, `|`, o revise la lista de exclusión `!|`.
- **Faltan los tres módulos de caché de buffers** — `backend used buffer cache`, `checkpoints buffer cache` y `cleaned buffer cache` no están disponibles en PostgreSQL 17 y posteriores.
- **Una base de datos desapareció de la monitorización** — active **Enable entities file re-scan interval** para conservar su módulo `connection` y dejar que pase a crítico en lugar de eliminarlo.
- **Las estadísticas de consultas son siempre cero** — los módulos `queries`, `insert`, `delete` y `update` cuentan sentencias activas durante el último intervalo. Una instancia en reposo informa legítimamente de cero.
- **Una consulta personalizada no produce módulo** — solo se aceptan sentencias `SELECT`; cualquier otra se descarta con un aviso. Una consulta cuyo `target_scope` no encaja con el agente (por ejemplo `databases` en el agente de instancia) también se omite.
- **Se ignora una expresión crontab no válida** — el `crontab` de una consulta personalizada debe tener cinco campos. Una expresión no válida genera un aviso y la consulta se omite.

## Referencia

### Parámetros de la tarea

#### PostgreSQL Base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| PostgreSQL target strings | `_dbstrings_` | textarea | — | Obligatorio. Separados por comas o uno por línea. `#` comenta una línea. Cada entrada crea un agente principal. Consulte [Cadenas de destino](#cadenas-de-destino) |
| PostgreSQL Credentials | `_credentials_` | select | — | Obligatorio. Credencial **Custom** del almacén de credenciales. Consulte [Crear la credencial](#crear-la-credencial) |

#### PostgreSQL Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Max threads | `_threads_` | number | `1` | Hilos de monitorización concurrentes |
| Target agent | `_engineAgent_` | textarea | — | Nombres de agente, emparejados por posición con las cadenas de destino. Vacío usa la dirección del destino |
| Custom module prefix | `_prefixModuleName_` | string | — | Se antepone a todos los nombres de módulo generados |
| Autodisabled agents | `_autodisabledAgents_` | checkbox | desactivado | Crea los agentes generados en modo Autodisabled |
| Scan databases | `_scanDatabases_` | checkbox | desactivado | Descubre las bases de datos de cada instancia |
| Create agent per database | `_agentPerDatabase_` | checkbox | desactivado | Un agente por cada base de datos descubierta |
| Custom database agent prefix | `_prefixAgent_` | string | — | Visible cuando **Create agent per database** está activado. Se antepone a los nombres de los agentes por base de datos |
| Enable entities file re-scan interval | `_enableEntitiesInterval_` | checkbox | desactivado | Persiste y revalida la lista de bases de datos descubiertas |
| Re-scan entities file interval | `_entitiesInterval_` | select | `86400` | Visible cuando **Enable entities file re-scan interval** está activado. Intervalo de refresco |
| Check engine uptime | `_checkUptime_` | checkbox | activado | Crea el módulo de detección de reinicios |
| Retrieve query statistics | `_queryStats_` | checkbox | activado | Crea los módulos `queries`, `insert`, `delete` y `update` |
| Analyze connections | `_checkConnections_` | checkbox | activado | Crea el módulo de uso de sesiones |
| Calculate fragmentation ratio | `_checkFragmentation_` | checkbox | activado | Crea el módulo de ratio de fragmentación |
| Retrieve cache statistics | `_checkCache_` | checkbox | activado | Crea los módulos de caché de buffers |
| Storage statistics | `_checkStorage_` | checkbox | activado | Crea los módulos de almacenamiento por base de datos |
| Query performance | `_checkQueryPerformance_` | checkbox | activado | Crea los módulos de rendimiento de consultas |
| Connections statistics | `_checkConnectionStats_` | checkbox | activado | Crea los módulos de conexiones por base de datos |
| Transaction statistics | `_checkTransactionStats_` | checkbox | activado | Crea los módulos de transacciones |
| Table statistics | `_checkTableStats_` | checkbox | activado | Crea los módulos de estadísticas de tablas |
| Advanced performance | `_checkAdvancedPerf_` | checkbox | activado | Crea los módulos de blocks read y blocks hit |
| Execute custom queries | `_executeCustomQueries_` | checkbox | activado | Habilita el bloque de consultas personalizadas |
| Custom queries | `_customQueries_` | textarea | — | Visible cuando **Execute custom queries** está activado. Consulte [Referencia de consultas personalizadas](#referencia-de-consultas-personalizadas) |

### Cadenas de destino

El campo **PostgreSQL target strings** acepta un destino por línea o separados por comas. Las líneas vacías y las que empiezan por `#` se ignoran. Cada destino usa `HOST` o `HOST:PORT`, opcionalmente con una selección de bases de datos:

| Formato | Significado |
|---------|-------------|
| `HOST` | Solo la instancia, salvo que **Scan databases** esté activado |
| `HOST:PORT` | La instancia en el puerto indicado |
| `HOST:PORT\DATABASE` | La instancia más esa base de datos |
| `HOST:PORT\|db1;db2;db3` | La instancia más las bases de datos listadas |
| `HOST:PORT!\|db1;db2` | La instancia más todas las bases de datos descubiertas excepto las listadas (requiere **Scan databases**) |

Ejemplos:

```
172.17.0.3:5432\postgres
172.17.0.4:5432|pandora;metadata
172.17.0.5:5432!|template0;template1
# Esta línea es un comentario y se ignora
172.17.0.6:5432
```

### Fichero de configuración

Una tarea de Discovery construye este fichero a partir de sus propios campos. Una ejecución manual lo proporciona con `--conf`.

| Clave | Descripción |
| --- | --- |
| `agents_group_id` | Id del grupo asignado a los agentes generados |
| `interval` | Intervalo de agente y módulo, en segundos |
| `credentials` | JSON codificado en Base64 con los campos `user` y `password`. Tiene precedencia sobre `user` y `password` |
| `user`, `password` | Credenciales de conexión en claro, se usan cuando `credentials` no está definido |
| `threads` | Número de hilos de monitorización concurrentes |
| `modules_prefix` | Prefijo de los nombres de módulo generados |
| `autodisabled_agents` | `1` crea los agentes generados en modo Autodisabled |
| `scan_databases` | `1` descubre las bases de datos de cada instancia |
| `agent_per_database` | `1` crea un agente por cada base de datos descubierta |
| `db_agent_prefix` | Prefijo de los nombres de los agentes por base de datos |
| `execute_custom_queries` | `1` ejecuta las consultas personalizadas |
| `analyze_connections` | `1` crea el módulo de uso de sesiones |
| `engine_uptime` | `1` crea el módulo de detección de reinicios |
| `query_stats` | `1` crea los módulos de estadísticas de consultas de instancia |
| `cache_stats` | `1` crea los módulos de caché de buffers |
| `fragmentation_ratio` | `1` crea el módulo de ratio de fragmentación |
| `check_storage_stats` | `1` crea los módulos de almacenamiento |
| `check_query_performance` | `1` crea los módulos de rendimiento de consultas |
| `check_connection_stats` | `1` crea los módulos de conexiones por base de datos |
| `check_transaction_stats` | `1` crea los módulos de transacciones |
| `check_table_stats` | `1` crea los módulos de estadísticas de tablas |
| `check_advanced_perf` | `1` crea los módulos de rendimiento avanzado |
| `entities_list` | Ruta del fichero donde se almacenan las bases de datos descubiertas |
| `enable_entities_interval` | `1` habilita el reescaneo de la lista de bases de datos |
| `entities_interval` | Intervalo de reescaneo, en segundos |
| `cron_state_dir` | Directorio donde se almacena la última ejecución correcta de las consultas programadas |

Ejemplo:

```ini
agents_group_id=10
interval=300
user=<USERNAME>
password=<PASSWORD>
threads=1
modules_prefix=
execute_custom_queries=1
analyze_connections=1
engine_uptime=1
query_stats=1
fragmentation_ratio=1
cache_stats=1
scan_databases=1
agent_per_database=1
db_agent_prefix=
entities_list=/tmp/postgresql_entities_list.txt
enable_entities_interval=1
entities_interval=300
check_storage_stats=1
check_query_performance=1
check_connection_stats=1
check_transaction_stats=1
check_table_stats=1
check_advanced_perf=1
```

> El valor de `credentials` es JSON codificado en Base64, que es reversible, no cifrado. Proteja el fichero de configuración como un secreto. Cuando la credencial se almacena en el almacén de credenciales de Pandora FMS, la tarea no escribe la contraseña en el fichero generado.

### Ejecución por línea de comandos

El plugin se puede ejecutar a mano, lo que es la forma más rápida de confirmar un destino y sus credenciales antes de llevarlos a una tarea.

```bash
./pandora_postgresql \
    --conf <PATH_TO_CONFIG> \
    --target_databases <PATH_TO_TARGETS> \
    [ --target_agents <PATH_TO_AGENT_NAMES> ] \
    [ --custom_queries <PATH_TO_CUSTOM_QUERIES> ]
```

| Parámetro | Descripción |
| --- | --- |
| `--conf` | Ruta del fichero de configuración |
| `--target_databases` | Ruta del fichero que contiene las bases de datos de destino |
| `--target_agents` | Ruta del fichero que contiene los nombres de agente, emparejados por posición con los destinos |
| `--custom_queries` | Ruta del fichero que contiene las consultas personalizadas |

La ejecución devuelve un resumen JSON. Los datos recogidos se exponen en el campo `monitoring_data` del resumen para que los consuma el servidor de Discovery.

Un `--conf` manual puede autenticarse con `credentials` (JSON codificado en Base64 con `user` y `password`) o con las claves en claro `user` y `password`. Cuando están presentes ambas, gana `credentials`.

### Referencia de consultas personalizadas

Cada consulta personalizada es un bloque delimitado por `check_begin` y `check_end`. Solo se permiten sentencias `SELECT`.

| Clave | Descripción |
| --- | --- |
| `name` | Nombre del módulo. Obligatorio. Admite `$__self_dbname` |
| `description` | Descripción del módulo |
| `target` | Consulta SQL a ejecutar. Obligatorio. Solo se aceptan sentencias `SELECT`. Se acepta `sql` como sinónimo. Admite `$__self_dbname` |
| `target_scope` | `instances`, `databases` o `all`. Por defecto `all` |
| `target_databases` | Nombres de base de datos separados por comas a los que aplica la consulta. `all` o vacío la aplica a todas. En el nivel de instancia, `postgres` casa con la instancia |
| `operation` | `value` devuelve un único valor; `full` devuelve todas las filas como una cadena |
| `datatype` | `generic_data`, `generic_data_string` o `generic_proc`. Las operaciones `full` se fuerzan a `generic_data_string` |
| `min_warning`, `max_warning` | Umbrales de warning |
| `min_critical`, `max_critical` | Umbrales de critical |
| `warning_inverse`, `critical_inverse` | Poner a `1` para invertir el intervalo de umbral correspondiente |
| `str_warning`, `str_critical` | Umbrales de cadena |
| `module_interval` | Intervalo del módulo como múltiplo del intervalo del agente |
| `crontab` | Expresión cron de cinco campos. Cuando está presente, la consulta solo se ejecuta cuando vence una ocurrencia |

Ejemplo:

```
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

La palabra reservada `$__self_dbname` se sustituye por la base de datos donde se ejecuta la consulta (o `postgres` en el nivel de instancia) tanto en `target` como en `name`. La consola incluye una guía comentada del formato como contenido por defecto del área de texto **Custom queries**.

### Módulos generados

Todos los nombres de módulo llevan el **Custom module prefix** cuando se define.

#### Agente principal

| Módulo | Tipo | Unidad | Se activa con |
|--------|------|--------|---------------|
| `<prefix>POSTGRESQL connection` | `generic_proc` | — | Siempre |
| `<prefix>restart detection` | `generic_proc` | — | Check engine uptime |
| `<prefix>queries`, `<prefix>insert`, `<prefix>delete`, `<prefix>update` | `generic_data` | — | Retrieve query statistics |
| `<prefix>session usage` | `generic_data` | % | Analyze connections |
| `<prefix>allocated buffer cache`, `<prefix>backend used buffer cache`, `<prefix>checkpoints buffer cache`, `<prefix>cleaned buffer cache` | `generic_data` | bytes | Retrieve cache statistics |

#### Módulos de base de datos

Una base de datos monitorizada produce siempre su módulo `connection`. El resto depende de los grupos activados, como se detalla en [Módulos de base de datos](#modulos-de-base-de-datos).

Con **Create agent per database** activado, cada base de datos tiene su propio agente y sus módulos usan los nombres simples (`connection`, `database size`, ...). Con la opción desactivada, los módulos se añaden al agente principal y cada nombre lleva el prefijo de la base de datos (`<prefix><database> connection`, `<prefix><database> database size`, ...).

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la aplicación | `pandorafms.postgresql` |
| Versión del plugin | `1.6` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
| Disponibilidad | Marketplace de Pandora FMS (`pandorafms.postgresql`) |
