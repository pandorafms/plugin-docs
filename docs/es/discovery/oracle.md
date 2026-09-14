# Oracle Discovery

*Última actualización del artículo: 2026-09-14.*

## Qué monitoriza

El plugin de Discovery de Oracle monitoriza bases de datos Oracle ejecutando consultas SQL contra ellas y convirtiendo los resultados en módulos de monitorización de Pandora FMS. Recoge disponibilidad, uso de sesiones y conexiones, número de consultas, detección de reinicios, uso y estado de los tablespaces, fragmentación, ratios de acierto de caché y cualquier consulta SQL personalizada que defina el operador.

El plugin crea **un agente por cada base de datos de destino**. Cuando el destino es una base de datos contenedora (CDB) multitenant de Oracle, además puede descubrir sus bases de datos conectables (PDB) y monitorizarlas dentro del agente contenedor o como **un agente por cada PDB**.

El plugin está pensado para usarse a través del sistema **Discovery** de Pandora FMS. No genera ficheros XML de agente: devuelve los agentes y módulos descubiertos en la salida JSON de la ejecución, y la tarea de Discovery los crea.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Versión del plugin `1.9` (`pandorafms.oracle`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| CDB/PDB multitenant de Oracle cuyos servicios de PDB están registrados en el listener bajo un nombre con `db_domain` | `Probado` | Ejecución de verificación del ticket #24889: la tarea terminó con `Targets up` y generó el agente de PDB y sus módulos. Consulte [Resolución del servicio de PDB en multitenant](#resolucion-del-servicio-de-pdb-en-multitenant) |
| Alcance de red desde el servidor de Discovery a cada listener de base de datos de destino | `Requerido` | El plugin abre una conexión Oracle remota por cada destino |
| Oracle Instant Client, cuando se activa **Thick mode** | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Prerrequisitos](#prerrequisitos) |
| Oracle Database 11 o anterior | `Sin validar` | La guía rápida oficial indica que se necesita thick mode para Oracle 11 y anteriores |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | No se ha registrado ningún sistema operativo de host |
| Versiones del servidor Oracle Database | `Sin validar` | La compatibilidad se estableció contra las consultas SQL y el contrato de conexión, no contra una matriz de versiones |

### Prerrequisitos

1. **Conectividad de red** entre el servidor de Discovery y cada listener de base de datos de destino.
2. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.
3. **Un usuario de base de datos** con permiso para conectarse y con privilegios `SELECT` sobre las vistas que usan los módulos que se activen.
4. **Oracle Instant Client** instalado en el servidor de Discovery, solo cuando se use **Thick mode**.

El plugin se distribuye como una aplicación de Discovery autocontenida: el paquete `.disco` incluye su propio ejecutable, por lo que no hay que instalar ningún runtime adicional para una ejecución normal.

### Conceder los privilegios necesarios

El usuario de conexión necesita al menos el privilegio `CREATE SESSION`:

```sql
GRANT CREATE SESSION TO pandora;
```

Cada módulo lee vistas concretas de Oracle. Conceda solo lo que necesiten los módulos activados.

| Grupo de módulos | Vistas de Oracle | Concesión |
|------------------|------------------|-----------|
| Connections (`checkConnections`) | `V$SESSION`, `V$PARAMETER` | `GRANT SELECT ON V_$SESSION TO pandora;`<br>`GRANT SELECT ON V_$PARAMETER TO pandora;` |
| Uptime (`checkUptime`) | `V$SESSION` | `GRANT SELECT ON V_$SESSION TO pandora;` |
| Query statistics (`queryStats`) | `V$SQLSTATS` | `GRANT SELECT ON V_$SQLSTATS TO pandora;` |
| Tablespaces (`checkTablespaces`) | `DBA_TABLESPACE_USAGE_METRICS`, `DBA_TABLESPACES` y `DBA_DATA_FILES` / `DBA_FREE_SPACE` para el fallback de Oracle 10g y anteriores | `GRANT SELECT ON DBA_TABLESPACE_USAGE_METRICS TO pandora;`<br>`GRANT SELECT ON DBA_TABLESPACES TO pandora;`<br>`GRANT SELECT ON DBA_DATA_FILES TO pandora;`<br>`GRANT SELECT ON DBA_FREE_SPACE TO pandora;` |
| Fragmentation (`checkFragmentation`) | `DBA_TABLES` | `GRANT SELECT ON DBA_TABLES TO pandora;` |
| Cache (`checkCache`) | `V$LIBRARYCACHE`, `V$ROWCACHE`, `V$SYSSTAT` | `GRANT SELECT ON V_$LIBRARYCACHE TO pandora;`<br>`GRANT SELECT ON V_$ROWCACHE TO pandora;`<br>`GRANT SELECT ON V_$SYSSTAT TO pandora;` |
| Descubrimiento de PDB multitenant (`multitenant`) | `V$PDBS` y `V$ACTIVE_SERVICES` | `GRANT SELECT ON V_$PDBS TO pandora;`<br>`GRANT SELECT ON V_$ACTIVE_SERVICES TO pandora;` |
| Versión de la base de datos | `PRODUCT_COMPONENT_VERSION` | `GRANT SELECT ON PRODUCT_COMPONENT_VERSION TO pandora;` |
| Consultas personalizadas | Depende de la consulta | Conceda `SELECT` sobre cualquier tabla o vista que referencien las consultas personalizadas |

> La versión `1.9` lee `V$ACTIVE_SERVICES` para resolver el nombre de servicio del listener de cada PDB. Sin esta concesión, la consulta de descubrimiento de PDB multitenant falla y no se monitoriza ningún PDB.

Por comodidad, `SELECT_CATALOG_ROLE` cubre la mayoría de las vistas `V$` y `DBA_`:

```sql
CREATE USER pandora IDENTIFIED BY <PASSWORD>;
GRANT CREATE SESSION TO pandora;
GRANT SELECT_CATALOG_ROLE TO pandora;
```

Cuando se use monitorización multitenant, el usuario también debe poder conectarse a **cada PDB** y tener las concesiones de módulos dentro de él:

```sql
ALTER SESSION SET CONTAINER = <PDB_NAME>;
GRANT CREATE SESSION TO pandora;
-- Repita las concesiones de módulos dentro del PDB.
```

### Instalar el plugin

Cargue el paquete `.disco` de `pandorafms.oracle` desde el marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/entries/pandorafms.oracle](https://marketplace.pandorafms.com/entries/pandorafms.oracle)

Una vez cargado, la aplicación **Oracle** queda disponible al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Oracle**. La consola presenta los campos en dos pasos: **Oracle Base** y **Oracle Detailed**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Oracle Base** — los destinos y cómo alcanzarlos:

    - **Oracle target strings**: uno o varios destinos Oracle, separados por comas o uno por línea. Cada línea crea un agente. Consulte [Cadenas de destino](#cadenas-de-destino).
    - **User** y **Password**: credenciales usadas para todos los destinos de la tarea.
    - **Thick mode** y **Client path**: use el Oracle Instant Client; la ruta del cliente es obligatoria cuando se activa thick mode.
    - **Multitenant: Discover and monitor PDBs within a CDB**: activa el descubrimiento de PDB en arquitecturas multitenant.
    - **Create agent per PDB**: crea un agente independiente por cada PDB descubierto en lugar de añadir sus módulos al agente contenedor.
    - **Enable entities file re-scan interval** y **Re-scan entities file interval**: mantienen y refrescan periódicamente la lista de PDB descubiertos.

    ![Paso Oracle Base de la tarea de Discovery, con las cadenas de destino, las credenciales, thick mode, multitenant y la opción de agente por PDB](../assets/images/discovery/oracle/oracle-task-base.png)

    En el ejemplo anterior, la cadena de destino `oracle-domain-mock:1521/FREE|PKI` monitoriza la base de datos contenedora `FREE` y restringe la monitorización multitenant al PDB `PKI`.

2. **Oracle Detailed** — alcance de la monitorización y ajustes opcionales:

    - **Max threads**: número de conexiones concurrentes usadas para monitorizar los destinos.
    - **Target agent**: nombres que se asignan a los agentes generados, emparejados por posición con las cadenas de destino. Si se deja vacío, se usa la cadena de destino como nombre del agente.
    - **Custom module prefix**: se antepone a todos los nombres de módulo generados.
    - **Check engine uptime**, **Retrieve query statistics**, **Analyze connections**, **Calculate fragmentation ratio**, **Monitor tablespaces**, **Retrieve cache statistics**: seleccionan los grupos de módulos que se crean.
    - **Execute custom queries** y **Custom queries**: ejecutan SQL definido por el operador y crean un módulo por consulta.
    - **Define tresholds**: umbrales por expresión regular aplicados a los módulos generados (excepto los módulos de consultas personalizadas). Consulte [Umbrales](#umbrales).

    ![Paso Oracle Detailed de la tarea de Discovery, con max threads, target agent, el prefijo de módulos, las casillas de módulos, las consultas personalizadas y los umbrales](../assets/images/discovery/oracle/oracle-task-detailed.png)

El grupo y el intervalo propios de la tarea, definidos en el paso genérico de la tarea, se convierten en el grupo de agentes y el intervalo de módulos.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea Oracle completada informa de:

    - **Total agents**: número de agentes generados por la tarea.
    - **Targets up**: destinos a los que el plugin se pudo conectar.
    - **Targets down**: destinos a los que no pudo conectarse.

    Con **Create agent per PDB** activado, `Total agents` incluye el agente contenedor más un agente por cada PDB monitorizado.

    ![Listado de tareas de Discovery con una tarea Oracle completada y su resumen de ejecución, con Targets down 0, Targets up 1 y Total agents 2](../assets/images/discovery/oracle/oracle-task-summary.png)

2. **Los agentes.** Uno por cada cadena de destino, más uno por cada PDB cuando **Create agent per PDB** está activado. Cada agente de PDB se llama `<agente contenedor> - PDB <nombre del pdb>`.

    ![Listado de agentes con el agente contenedor de Oracle y su agente de PDB](../assets/images/discovery/oracle/oracle-agents.png)

3. **Los módulos de cada agente.** Un destino alcanzable produce el módulo de disponibilidad y un módulo por cada grupo activado y recurso descubierto. La lista de módulos del agente de PDB muestra el servicio resuelto en el módulo de conexión y el prefijo `PDB PKI ` en cada métrica del PDB.

    ![Lista de módulos de un agente de PDB de Oracle, desde el módulo de conexión hasta los módulos de tablespace, consultas, caché y consultas personalizadas](../assets/images/discovery/oracle/oracle-pdb-modules.png)

Si la tarea informa de `Targets down` para un destino, revise [Resolución de problemas](#resolucion-de-problemas).

## Entender los resultados

### Agentes y cardinalidad

- **Un agente por cada cadena de destino.** El nombre del agente es la cadena de destino, salvo que se indique un nombre en **Target agent** para esa posición. El sistema operativo del agente se informa como `Oracle` y su versión de sistema operativo como la versión de la base de datos conectada.
- **Opcionalmente, un agente por PDB.** Cuando **Create agent per PDB** está activado, cada PDB descubierto tiene su propio agente llamado `<agente contenedor> - PDB <nombre del pdb>` y direccionado como `HOST:PORT/<nombre del pdb>`. Cuando está desactivado, los módulos de cada PDB se añaden al agente contenedor con el prefijo `PDB <nombre del pdb> `.

### Grupos de módulos

Un destino alcanzable siempre produce el módulo de disponibilidad `<prefix>Oracle connection`, con valor `1` cuando la conexión se estableció y `0` cuando no.

| Grupo | Módulos | Tipo | Notas |
|-------|---------|------|-------|
| Disponibilidad | `<prefix>Oracle connection` | `generic_proc` | `1` conectado, `0` no conectado |
| Uptime | `<prefix>restart detection` | `generic_proc` | `0` cuando el motor se reinició en los dos últimos intervalos, `1` en caso contrario |
| Estadísticas de consultas | `<prefix>queries: select`, `<prefix>queries: insert`, `<prefix>queries: delete`, `<prefix>queries: update` | `generic_data` | Número de sentencias de cada tipo activas durante el último intervalo |
| Tablespaces | `<prefix>tablespace <nombre> free` y `<prefix>tablespace <nombre> status` | `generic_data` (%) y `generic_proc` | Porcentaje libre y `1` cuando el tablespace está `ONLINE` |
| Conexiones | `<prefix>session usage` | `generic_data` (%) | Sesiones actuales frente al máximo configurado |
| Fragmentación | `<prefix>fragmentation ratio` | `generic_data` (%) | Ratio de fragmentación medio |
| Caché | `<prefix>cache hit ratio (dictionary)`, `<prefix>cache hit ratio (library)`, `<prefix>cache hit ratio (buffer)` | `generic_data` (%) | Con umbrales de warning/critical por defecto |
| Consultas personalizadas | `<prefix><nombre de la consulta>` | Según la consulta | Un módulo por consulta personalizada |

El inventario exhaustivo, con los prefijos de PDB y los umbrales por defecto, está en [Módulos generados](#modulos-generados).

### Resolución del servicio de PDB en multitenant

En Oracle multitenant, el nombre de un PDB no es necesariamente el nombre de servicio que expone el listener. Un PDB puede existir mientras su servicio de listener solo está registrado con un nombre cualificado, por ejemplo cuando la base de datos tiene configurado un `db_domain`. En ese caso, conectarse solo con el nombre del PDB falla con `DPY-6001: Service "..." is not registered with the listener` (equivalente a `ORA-12514`).

La versión `1.9` resuelve esto descubriendo los nombres de servicio reales registrados para cada PDB y probándolos en orden:

1. Los nombres de servicio de listener registrados para ese PDB.
2. Esos mismos nombres cualificados con el dominio de la base de datos (`db_domain`) cuando el listener los expone como nombres totalmente cualificados.
3. El propio nombre del PDB, como último recurso.

Solo cuando fallan todos los candidatos se informa de un aviso y (con **Create agent per PDB**) se crea el agente de PDB con su módulo de conexión en valor `0`.

El campo **Oracle target strings** permite restringir qué PDB se monitorizan añadiendo `|<pdb>` o `|<pdb1>;<pdb2>;...` a un destino, como se muestra en [Configurar la tarea de Discovery](#configurar-la-tarea-de-discovery).

### Consultas personalizadas

Cada consulta personalizada genera un módulo en todos los agentes a los que aplica. Una consulta puede limitarse al ámbito del contenedor (`cdb`), a los PDB (`pdb`) o a ambos (`all`), y puede programarse con una expresión crontab de cinco campos. Las consultas programadas conservan su última ejecución correcta, de modo que una ocurrencia perdida mientras el plugin no se ejecutaba se ejecuta en la siguiente ejecución de la tarea. Consulte [Referencia de consultas personalizadas](#referencia-de-consultas-personalizadas).

## Resolución de problemas

El plugin informa de sus diagnósticos en el resumen JSON de ejecución que imprime en la salida estándar: los avisos de conexión, los códigos de error de Oracle y las consultas omitidas se añaden ahí.

- **`DPY-6001: Service "..." is not registered with the listener` (o `ORA-12514`)** — el servicio del PDB no es alcanzable con el nombre probado. La versión `1.9` resuelve automáticamente el nombre de servicio registrado y la cualificación con `db_domain`; si sigue fallando, compruebe que el usuario tiene `SELECT` sobre `V$ACTIVE_SERVICES` y que el servicio del PDB está realmente registrado en el listener.
- **`Targets down` en un destino** — falló la conexión al contenedor. Compruebe el acceso de red desde el servidor de Discovery, el formato de la cadena de destino y las credenciales.
- **No se descubre ningún PDB** — falló la consulta de descubrimiento (a menudo por falta de concesión sobre `V$PDBS` o `V$ACTIVE_SERVICES`), o ningún PDB coincide con el filtro `|PDB` de la cadena de destino.
- **Se omite un PDB** — solo se monitorizan los PDB en modo abierto `READ WRITE`; los PDB omitidos se nombran en el resumen de ejecución.
- **`ORA-00942: table or view does not exist`** — el usuario de monitorización carece de `SELECT` sobre una vista necesaria. Conceda el privilegio del grupo de módulos activado y vuelva a ejecutar.
- **`agent_per_pdb` no surte efecto** — solo se aplica cuando **Multitenant** está activado.
- **Se ignora una expresión crontab no válida** — el `crontab` de una consulta personalizada debe tener cinco campos. Una expresión no válida genera un aviso y la consulta se omite.
- **Thick mode no arranca** — **Client path** debe apuntar a las librerías del Oracle Instant Client instaladas en el servidor de Discovery.

## Referencia

### Parámetros de la tarea

#### Oracle Base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Oracle target strings | `_dbstrings_` | textarea | — | Obligatorio. Separados por comas o uno por línea. `#` comenta una línea. Cada entrada crea un agente. Consulte [Cadenas de destino](#cadenas-de-destino) |
| User | `_dbuser_` | string | — | Obligatorio. Usuario de conexión |
| Password | `_dbpass_` | password | — | Obligatorio. Contraseña de conexión |
| Thick mode | `_thickMode_` | checkbox | desactivado | Usa el Oracle Instant Client en lugar del modo de driver por defecto |
| Client path | `_clientPath_` | string | — | Visible cuando **Thick mode** está activado. Ruta a las librerías del Oracle Instant Client |
| Multitenant: Discover and monitor PDBs within a CDB | `_multiTenant_` | checkbox | desactivado | Descubre PDB en arquitecturas multitenant; en entornos no CDB emite un aviso inofensivo |
| Create agent per PDB | `_agentPerPdb_` | checkbox | desactivado | Visible cuando **Multitenant** está activado. Un agente por PDB en lugar de módulos en el agente contenedor |
| Enable entities file re-scan interval | `_enableEntitiesInterval_` | checkbox | desactivado | Visible cuando **Multitenant** está activado. Refresca periódicamente la lista de PDB descubiertos |
| Re-scan entities file interval | `_entitiesInterval_` | select | `86400` | Visible cuando **Enable entities file re-scan interval** está activado. Intervalo de refresco, en los intervalos que ofrece el selector |

#### Oracle Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Max threads | `_threads_` | number | `1` | Hilos de monitorización concurrentes |
| Target agent | `_engineAgent_` | textarea | — | Nombres de agente, emparejados por posición con las cadenas de destino. Vacío usa la cadena de destino |
| Custom module prefix | `_prefixModuleName_` | string | — | Se antepone a todos los nombres de módulo generados |
| Check engine uptime | `_checkUptime_` | checkbox | activado | Crea el módulo de detección de reinicios |
| Retrieve query statistics | `_queryStats_` | checkbox | desactivado | Crea los módulos `queries:` |
| Analyze connections | `_checkConnections_` | checkbox | activado | Crea el módulo de uso de sesiones |
| Calculate fragmentation ratio | `_checkFragmentation_` | checkbox | activado | Crea el módulo de ratio de fragmentación |
| Monitor tablespaces | `_checkTablespaces_` | checkbox | activado | Crea los módulos de tablespace free y status |
| Retrieve cache statistics | `_checkCache_` | checkbox | activado | Crea los módulos de cache hit ratio |
| Execute custom queries | `_executeCustomQueries_` | checkbox | activado | Habilita el bloque de consultas personalizadas |
| Custom queries | `_customQueries_` | textarea | — | Visible cuando **Execute custom queries** está activado. Consulte [Referencia de consultas personalizadas](#referencia-de-consultas-personalizadas) |
| Define tresholds | `_configTresholds_` | textarea | — | Visible siempre. Consulte [Umbrales](#umbrales) |

### Cadenas de destino

El campo **Oracle target strings** acepta un destino por línea o separados por comas. Las líneas vacías y las que empiezan por `#` se ignoran. Cada destino puede usar cualquiera de estos formatos:

```
HOST/SID
HOST:PORT/SID
HOST:PORT/SERVICE_NAME
dsn=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=<HOST>)(PORT=1521))(CONNECT_DATA=(SID=<SID>)))
```

Cuando se omite el puerto, se usa `1521`.

Una cadena DSN completa también puede describir una configuración de failover con varias direcciones:

```
dsn=(DESCRIPTION=(FAILOVER=ON)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=<HOST_1>)(PORT=1521))(ADDRESS=(PROTOCOL=TCP)(HOST=<HOST_2>)(PORT=1521)))(CONNECT_DATA=(SID=<SID>)))
```

Cuando el destino es un contenedor multitenant y **Multitenant** está activado, se puede añadir un filtro de PDB con `|`:

```
HOST:PORT/SERVICE_NAME|PDB1
HOST:PORT/SERVICE_NAME|PDB1;PDB2
```

Sin filtro, se monitorizan todos los PDB elegibles.

### Fichero de configuración

Una tarea de Discovery construye este fichero a partir de sus propios campos. Una ejecución manual lo proporciona con `--conf`.

| Clave | Descripción |
| --- | --- |
| `agents_group_id` | Id del grupo asignado a los agentes generados |
| `interval` | Intervalo de agente y módulo, en segundos |
| `user` | Usuario de conexión |
| `password` | Contraseña de conexión |
| `thick_mode` | `1` activa thick mode |
| `client_path` | Ruta a las librerías del Oracle Instant Client; se usa con thick mode |
| `threads` | Número de hilos de monitorización concurrentes |
| `modules_prefix` | Prefijo de los nombres de módulo generados |
| `multitenant` | `1` descubre y monitoriza PDB |
| `agent_per_pdb` | `1` crea un agente por PDB; requiere `multitenant=1` |
| `execute_custom_queries` | `1` ejecuta las consultas personalizadas |
| `analyze_connections` | `1` crea el módulo de uso de sesiones |
| `engine_uptime` | `1` crea el módulo de detección de reinicios |
| `query_stats` | `1` crea los módulos de estadísticas de consultas |
| `cache_stats` | `1` crea los módulos de cache hit ratio |
| `fragmentation_ratio` | `1` crea el módulo de ratio de fragmentación |
| `check_tablescpaces` | `1` crea los módulos de tablespace |
| `entities_list` | Ruta del fichero donde se almacenan los PDB descubiertos |
| `enable_entities_interval` | `1` habilita el reescaneo de la lista de PDB |
| `entities_interval` | Intervalo de reescaneo, en segundos |
| `cron_state_dir` | Directorio donde se almacena la última ejecución correcta de las consultas programadas |

Ejemplo:

```ini
[CONF]
agents_group_id=10
interval=300
user=<USERNAME>
password=<PASSWORD>
thick_mode=0
multitenant=1
agent_per_pdb=1
execute_custom_queries=1
analyze_connections=1
engine_uptime=1
query_stats=0
cache_stats=1
fragmentation_ratio=1
check_tablescpaces=1
```

### Ejecución por línea de comandos

El plugin se puede ejecutar a mano, lo que es la forma más rápida de confirmar un destino y sus credenciales antes de llevarlos a una tarea.

```bash
./pandora_oracle \
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

### Referencia de consultas personalizadas

Cada consulta personalizada es un bloque delimitado por `check_begin` y `check_end`. Solo se permiten sentencias `SELECT`.

| Clave | Descripción |
| --- | --- |
| `name` | Nombre del módulo. Obligatorio |
| `description` | Descripción del módulo |
| `target` | Consulta SQL a ejecutar. Obligatorio. Solo se aceptan sentencias `SELECT` |
| `target_databases` | Cadenas de destino (o nombres de PDB) separados por comas a los que aplica la consulta. `all` o vacío la aplica a todos |
| `target_scope` | `cdb`, `pdb` o `all`. Por defecto `cdb`. `pdb` requiere monitorización multitenant |
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
name Invalid objects count
description Number of invalid objects
operation value
datatype generic_data
min_warning 5
target SELECT COUNT(*) FROM ALL_OBJECTS WHERE STATUS != 'VALID'
target_scope all
check_end
```

La consola incluye una guía comentada del formato, y una colección de consultas de ejemplo, como contenido por defecto del área de texto **Custom queries**.

### Umbrales

El campo **Define tresholds** aplica umbrales a los módulos generados por nombre de módulo, excepto a los módulos de consultas personalizadas. Una definición por línea, con una expresión regular que casa con el nombre del módulo y los umbrales separados por `|`:

```
<REGEX> = <umbral>|<umbral>|...
```

Ejemplo:

```
^tablespace = min_warning 10|max_warning 20|min_critical 0|max_critical 10
```

### Módulos generados

Todos los nombres de módulo llevan el **Custom module prefix** cuando se define. Los módulos creados para un PDB mantienen el prefijo del contenedor y añaden un segmento `PDB <nombre del pdb> `.

#### Agente contenedor

| Módulo | Tipo | Grupo | Se activa con |
|--------|------|-------|---------------|
| `<prefix>Oracle connection` | `generic_proc` | Disponibilidad | Siempre |
| `<prefix>restart detection` | `generic_proc` | Uptime | Check engine uptime |
| `<prefix>queries: select` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefix>queries: insert` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefix>queries: delete` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefix>queries: update` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefix>tablespace <nombre> free` | `generic_data` | Tablespaces | Monitor tablespaces |
| `<prefix>tablespace <nombre> status` | `generic_proc` | Tablespaces | Monitor tablespaces |
| `<prefix>session usage` | `generic_data` | Conexiones | Analyze connections |
| `<prefix>fragmentation ratio` | `generic_data` | Fragmentación | Calculate fragmentation ratio |
| `<prefix>cache hit ratio (dictionary)` | `generic_data` | Caché | Retrieve cache statistics |
| `<prefix>cache hit ratio (library)` | `generic_data` | Caché | Retrieve cache statistics |
| `<prefix>cache hit ratio (buffer)` | `generic_data` | Caché | Retrieve cache statistics |
| `<prefix><nombre de la consulta>` | Según la consulta | Consultas personalizadas | Execute custom queries |

Los módulos de cache hit ratio llevan umbrales por defecto:

| Módulo | `max_warning` | `max_critical` |
|--------|---------------|----------------|
| `cache hit ratio (dictionary)` | `98` | `40` |
| `cache hit ratio (library)` | `98` | `40` |
| `cache hit ratio (buffer)` | `89` | `40` |

#### Módulos de PDB (Create agent per PDB desactivado)

Los mismos módulos que el agente contenedor, con `PDB <nombre del pdb> ` insertado después del prefijo personalizado, por ejemplo `<prefix>PDB <nombre del pdb> tablespace <nombre> free`.

#### Agente de PDB (Create agent per PDB activado)

Cada agente de PDB se llama `<agente contenedor> - PDB <nombre del pdb>` y se direcciona como `HOST:PORT/<nombre del pdb>`. Contiene:

- `<prefix>Oracle PDB <nombre del pdb> connection` (disponibilidad)
- Todos los grupos de módulos activados, con el prefijo `PDB <nombre del pdb> `
- Las consultas personalizadas cuyo ámbito aplica a los PDB

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la aplicación | `pandorafms.oracle` |
| Versión del plugin | `1.9` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
| Disponibilidad | Marketplace de Pandora FMS (`pandorafms.oracle`) |
