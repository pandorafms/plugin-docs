# Oracle Discovery

*Última actualización del artículo: 2026-09-25.*

## Qué monitoriza

El plugin de Discovery de Oracle monitoriza instancias de Oracle Database ejecutando consultas SQL contra ellas y convirtiendo sus resultados en módulos de monitorización de Pandora FMS. Recoge disponibilidad, uso de sesiones y conexiones, número de consultas, detección de reinicios, uso y estado de los tablespaces, fragmentación, ratios de acierto de caché y cualquier consulta SQL personalizada que defina el operador.

El plugin crea **un agente por base de datos objetivo**. Cuando un objetivo es una base de datos contenedora (CDB) de Oracle multitenant, además puede descubrir sus bases de datos conectables (PDB) y monitorizarlas dentro del agente contenedor o como **un agente por PDB**.

Un objetivo puede escribirse como una cadena simple `HOST:PORT/SERVICE` o como un descriptor DSN completo de Oracle. Los descriptores DSN conservan el failover con varias direcciones y también se usan para alcanzar las PDB, cuyo nombre se sustituye como nombre de servicio.

El plugin está pensado para usarse a través del sistema de **Discovery** de Pandora FMS. No genera archivos XML de agente: devuelve los agentes y módulos descubiertos en la salida JSON de la ejecución, y la tarea de Discovery los crea.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|-------|-------|----------|
| Versión del plugin `1.12` (`pandorafms.oracle`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Accesibilidad de red desde el servidor de Discovery a cada listener de base de datos objetivo | `Requerido` | El plugin abre una conexión remota de Oracle por objetivo |
| Un usuario de base de datos capaz de conectarse y con `SELECT` sobre las vistas usadas por los módulos habilitados | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Conceder los privilegios necesarios](#conceder-los-privilegios-necesarios) |
| Oracle Instant Client en el servidor de Discovery, cuando **Thick mode** está habilitado | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Requisitos](#requisitos) |
| Una versión concreta de Pandora FMS | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión de consola o de servidor |
| Un sistema operativo concreto del host que ejecuta el plugin | `Sin validar` | No se ha registrado ningún sistema operativo del host |
| Versiones del servidor de Oracle Database | `Sin validar` | La compatibilidad se estableció contra las consultas SQL y el contrato de conexión, no contra una matriz de versiones |

### Requisitos

1. **Conectividad de red** entre el servidor de Discovery y cada listener de base de datos objetivo.
2. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea, y la consola para definirla.
3. **Un usuario de base de datos** con permiso para conectarse y con privilegios `SELECT` sobre las vistas usadas por los módulos que habilite.
4. **Oracle Instant Client** instalado en el servidor de Discovery, solo cuando se use **Thick mode**.

El plugin se distribuye como una aplicación de Discovery autocontenida: el paquete `.disco` incluye su propio ejecutable, por lo que no hay que instalar ningún runtime adicional para una ejecución normal.

### Conceder los privilegios necesarios

El usuario de conexión necesita al menos el privilegio `CREATE SESSION`:

```sql
GRANT CREATE SESSION TO pandora;
```

Cada módulo lee vistas concretas de Oracle. Conceda solo lo que necesiten los módulos habilitados.

| Grupo de módulos | Vistas de Oracle | Concesión |
|--------------|--------------|-------|
| Conexiones (`checkConnections`) | `V$SESSION`, `V$PARAMETER` | `GRANT SELECT ON V_$SESSION TO pandora;`<br>`GRANT SELECT ON V_$PARAMETER TO pandora;` |
| Uptime (`checkUptime`) | `V$SESSION` | `GRANT SELECT ON V_$SESSION TO pandora;` |
| Estadísticas de consultas (`queryStats`) | `V$SQLSTATS` | `GRANT SELECT ON V_$SQLSTATS TO pandora;` |
| Tablespaces (`checkTablespaces`) | `DBA_TABLESPACE_USAGE_METRICS`, `DBA_TABLESPACES`, y `DBA_DATA_FILES` / `DBA_FREE_SPACE` para el método alternativo de Oracle 10 y anteriores | `GRANT SELECT ON DBA_TABLESPACE_USAGE_METRICS TO pandora;`<br>`GRANT SELECT ON DBA_TABLESPACES TO pandora;`<br>`GRANT SELECT ON DBA_DATA_FILES TO pandora;`<br>`GRANT SELECT ON DBA_FREE_SPACE TO pandora;` |
| Fragmentación (`checkFragmentation`) | `DBA_TABLES` | `GRANT SELECT ON DBA_TABLES TO pandora;` |
| Caché (`checkCache`) | `V$LIBRARYCACHE`, `V$ROWCACHE`, `V$SYSSTAT` | `GRANT SELECT ON V_$LIBRARYCACHE TO pandora;`<br>`GRANT SELECT ON V_$ROWCACHE TO pandora;`<br>`GRANT SELECT ON V_$SYSSTAT TO pandora;` |
| Descubrimiento de PDB multitenant (`multitenant`) | `V$PDBS` | `GRANT SELECT ON V_$PDBS TO pandora;` |
| Versión de la base de datos | `PRODUCT_COMPONENT_VERSION` | `GRANT SELECT ON PRODUCT_COMPONENT_VERSION TO pandora;` |
| Consultas personalizadas | Depende de la consulta | Conceda `SELECT` sobre cualquier tabla o vista a la que apunten las consultas personalizadas |

Por comodidad, `SELECT_CATALOG_ROLE` cubre la mayoría de vistas `V$` y `DBA_`:

```sql
CREATE USER pandora IDENTIFIED BY <PASSWORD>;
GRANT CREATE SESSION TO pandora;
GRANT SELECT_CATALOG_ROLE TO pandora;
```

Cuando se usa la monitorización multitenant, el usuario también debe poder conectarse a **cada PDB** y disponer de las concesiones de los módulos dentro de ella:

```sql
ALTER SESSION SET CONTAINER = <PDB_NAME>;
GRANT CREATE SESSION TO pandora;
-- Repita las concesiones de los módulos dentro de la PDB.
```

### Instalar el plugin

Cargue el paquete `.disco` de `pandorafms.oracle` desde el Marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/entries/pandorafms.oracle](https://marketplace.pandorafms.com/entries/pandorafms.oracle)

Una vez cargado, la aplicación **Oracle** está disponible al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Oracle**. La consola presenta los campos en dos pasos: **Oracle Base** y **Oracle Detailed**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Oracle Base** — los objetivos y cómo alcanzarlos:

    - **Oracle target strings**: uno o varios objetivos de Oracle, separados por comas o uno por línea. Cada línea crea un agente. Consulte [Cadenas objetivo](#cadenas-objetivo).
    - **User** y **Password**: credenciales usadas para cada objetivo de la tarea.
    - **Thick mode** y **Client path**: usan el Oracle Instant Client; la ruta del cliente es obligatoria cuando el modo thick está habilitado.
    - **Multitenant: Discover and monitor PDBs within a CDB**: habilita el descubrimiento de PDB en arquitecturas multitenant.
    - **Create agent per PDB**: crea un agente separado por cada PDB descubierta en lugar de añadir sus módulos al agente contenedor.
    - **Enable entities file re-scan interval** y **Re-scan entities file interval**: mantienen y refrescan periódicamente la lista de PDB descubiertas.

    ![Paso Oracle Base de la tarea de Discovery, con las cadenas objetivo, las credenciales, el modo thick y las opciones multitenant y de agente por PDB](../assets/images/discovery/oracle/oracle-task-base.png)

    En el ejemplo anterior, la cadena objetivo `oracle-domain-mock:1521/FREE|PKI` monitoriza la base de datos contenedora `FREE` y restringe la monitorización multitenant a la PDB `PKI`.

2. **Oracle Detailed** — alcance de la monitorización y ajustes opcionales:

    - **Max threads**: número de conexiones concurrentes usadas para monitorizar los objetivos.
    - **Target agent**: nombres que se asignan a los agentes generados, emparejados por posición con las cadenas objetivo. En blanco se usa la cadena objetivo como nombre del agente.
    - **Custom module prefix**: se antepone a todos los nombres de módulo generados.
    - **Check engine uptime**, **Retrieve query statistics**, **Analyze connections**, **Calculate fragmentation ratio**, **Monitor tablespaces**, **Retrieve cache statistics**: seleccionan los grupos de módulos que se crean.
    - **Execute custom queries** y **Custom queries**: ejecutan SQL definido por el operador y crean un módulo por consulta.
    - **Define tresholds**: umbrales por expresión regular aplicados a los módulos generados (excepto los módulos de consultas personalizadas). Consulte [Umbrales](#umbrales).

    ![Paso Oracle Detailed de la tarea de Discovery, con max threads, target agent, prefijo de módulo, las casillas de módulos, las consultas personalizadas y los umbrales](../assets/images/discovery/oracle/oracle-task-detailed.png)

El grupo y el intervalo propios de la tarea, definidos en el paso genérico de definición, se convierten en el grupo del agente y el intervalo de los módulos.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea de Oracle completada informa de:

    - **Total agents**: el número de agentes generados por la tarea.
    - **Targets up**: objetivos a los que el plugin se conectó.
    - **Targets down**: objetivos a los que no pudo conectarse.

    Con **Create agent per PDB** habilitado, `Total agents` incluye el agente contenedor más un agente por cada PDB monitorizada.

    ![Lista de tareas de Discovery con una tarea de Oracle completada y su resumen de ejecución mostrando Targets down 0, Targets up 1 y Total agents 2](../assets/images/discovery/oracle/oracle-task-summary.png)

2. **Los agentes.** Uno por cadena objetivo, más uno por PDB cuando **Create agent per PDB** está habilitado. Cada agente de PDB se llama `<agente contenedor> - PDB <nombre pdb>`.

    ![Lista de agentes mostrando el agente contenedor de Oracle y su agente de PDB](../assets/images/discovery/oracle/oracle-agents.png)

3. **Los módulos de cada agente.** Un objetivo alcanzable produce el módulo de disponibilidad y un módulo por cada grupo habilitado y recurso descubierto. La lista de módulos del agente de PDB muestra el prefijo `PDB PKI ` en cada métrica de la PDB.

    ![Lista de módulos de un agente de PDB de Oracle, desde el módulo de conexión hasta los módulos de tablespace, consultas, caché y consultas personalizadas](../assets/images/discovery/oracle/oracle-pdb-modules.png)

Si la tarea informa de `Targets down` para un objetivo, revise la sección [Solución de problemas](#solucion-de-problemas).

## Interpretar los resultados

### Agentes y cardinalidad

- **Un agente por cadena objetivo.** El nombre del agente es la cadena objetivo, salvo que se indique un nombre en **Target agent** para esa posición. En un objetivo simple, el filtro añadido tras `|` no forma parte del nombre del agente. En un objetivo DSN, el nombre es una etiqueta legible derivada del descriptor (`Oracle <HOST>:<PORT>/<SERVICE>`), con un hash corto añadido cuando el descriptor contiene varias direcciones o servicios. El sistema operativo del agente se informa como `Oracle` y su versión de sistema operativo como la versión de la base de datos conectada (o `Discovery` cuando no se puede leer).
- **Un agente por PDB, opcionalmente.** Cuando **Create agent per PDB** está habilitado, cada PDB descubierta obtiene su propio agente llamado `<agente contenedor> - PDB <nombre pdb>`. Su dirección es `HOST:PORT/<nombre pdb>`, o el mismo nombre generado cuando el objetivo es un descriptor DSN. Cuando la opción está deshabilitada, los módulos de cada PDB se añaden al agente contenedor con el prefijo `PDB <nombre pdb> `.

### Grupos de módulos

Un objetivo alcanzable siempre produce el módulo de disponibilidad `<prefijo>Oracle connection`, con valor `1` cuando la conexión tuvo éxito y `0` cuando no.

| Grupo | Módulos | Tipo | Notas |
|-------|---------|------|-------|
| Disponibilidad | `<prefijo>Oracle connection` | `generic_proc` | `1` conectado, `0` no conectado |
| Uptime | `<prefijo>restart detection` | `generic_proc` | `0` cuando el motor se reinició en los dos últimos intervalos, `1` en caso contrario |
| Estadísticas de consultas | `<prefijo>queries: select`, `<prefijo>queries: insert`, `<prefijo>queries: delete`, `<prefijo>queries: update` | `generic_data` | Número de sentencias de cada tipo activas durante el último intervalo |
| Tablespaces | `<prefijo>tablespace <nombre> free` y `<prefijo>tablespace <nombre> status` | `generic_data` (%) y `generic_proc` | Porcentaje libre y `1` cuando el tablespace está `ONLINE` |
| Conexiones | `<prefijo>session usage` | `generic_data` (%) | Sesiones actuales frente al máximo configurado |
| Fragmentación | `<prefijo>fragmentation ratio` | `generic_data` (%) | Ratio medio de fragmentación |
| Caché | `<prefijo>cache hit ratio (dictionary)`, `<prefijo>cache hit ratio (library)`, `<prefijo>cache hit ratio (buffer)` | `generic_data` (%) | Con umbrales de aviso/crítico por defecto |
| Consultas personalizadas | `<prefijo><nombre de consulta>` | Según la consulta | Un módulo por consulta personalizada |

El inventario exhaustivo, incluidos los prefijos de PDB y los umbrales por defecto, está en [Módulos generados](#modulos-generados).

### Conexión a PDB en multitenant

En Oracle multitenant, se llega a una PDB a través de su nombre de servicio. El plugin usa el propio nombre de la PDB como nombre de servicio al conectarse a ella, y lo adapta al formato del objetivo:

- **Objetivo simple** (`HOST:PORT/SERVICE`): el plugin se conecta a la PDB como `HOST:PORT/<nombre pdb>`.
- **Objetivo DSN**: el plugin reescribe el descriptor, sustituyendo el valor de `SERVICE_NAME` por el nombre de la PDB y conservando las direcciones, los puertos y la configuración de failover. Si el descriptor identifica la conexión con un `SID`, el plugin sustituye esa cláusula `SID` por `SERVICE_NAME=<nombre pdb>`.
- Si el descriptor no contiene ni `SERVICE_NAME` ni `SID`, no se puede construir la conexión a la PDB y esta se notifica en la información de ejecución y se omite.
- Un nombre de PDB que contenga caracteres fuera de letras, dígitos y `_ $ # . -` se rechaza como inválido.

Durante el descubrimiento solo se monitorizan las PDB en modo abierto `READ WRITE`; las demás se nombran en la información de ejecución y se omiten. Las PDB recuperadas del archivo de entidades se monitorizan según la caché.

El campo **Oracle target strings** permite restringir qué PDB se monitorizan añadiendo `|<pdb>` o `|<pdb1>;<pdb2>;...` a un objetivo, como se muestra en [Configurar la tarea de Discovery](#configurar-la-tarea-de-discovery).

### Consultas personalizadas

Cada consulta personalizada genera un módulo en cada agente al que se aplica. Una consulta puede limitarse al ámbito del contenedor (`cdb`), al de las PDB (`pdb`) o a ambos (`all`), y puede programarse con una expresión crontab de cinco campos. Las consultas programadas conservan su última ejecución correcta, de modo que una ocurrencia perdida mientras el plugin no se ejecutaba se ejecuta en la siguiente ejecución de la tarea. Consulte [Referencia de consultas personalizadas](#referencia-de-consultas-personalizadas).

## Solución de problemas

El plugin informa de su diagnóstico en el resumen JSON de ejecución impreso en la salida estándar: avisos de conexión, códigos de error de Oracle y consultas omitidas se añaden allí.

- **Un objetivo DSN no se puede conectar** — el plugin no recurre a una conexión `HOST:PORT/SID` cuando el objetivo es un descriptor DSN. Compruebe la sintaxis del descriptor y que sea alcanzable.
- **Una PDB se omite con `DSN contains no SERVICE_NAME or SID to replace`** — el objetivo DSN usado para alcanzar el contenedor no contiene un `SERVICE_NAME` ni un `SID` que sustituir por el nombre de la PDB. Use un descriptor que identifique la conexión con uno de ellos.
- **Una PDB se omite por inválida** — el nombre de la PDB contiene caracteres fuera de letras, dígitos y `_ $ # . -`.
- **`DPY-6001: Service "..." is not registered with the listener` (o `ORA-12514`)** — el servicio de la PDB no es alcanzable con el nombre que se probó. Verifique que el servicio de la PDB está registrado en el listener y que el plugin sustituye el nombre correcto.
- **`Targets down` para un objetivo** — la conexión al contenedor falló. Compruebe el acceso de red desde el servidor de Discovery, el formato de la cadena objetivo y las credenciales.
- **No se descubre ninguna PDB** — la consulta de descubrimiento falló (a menudo por falta de la concesión sobre `V$PDBS`), o ninguna PDB coincide con el filtro `|PDB` de la cadena objetivo.
- **Una PDB se omite** — solo se monitorizan las PDB en modo abierto `READ WRITE`; las omitidas se nombran en el resumen de ejecución.
- **`ORA-00942: table or view does not exist`** — el usuario de monitorización carece de `SELECT` sobre una vista requerida. Conceda el privilegio para el grupo de módulos habilitado y vuelva a ejecutar.
- **`agent_per_pdb` no tiene efecto** — solo se aplica cuando **Multitenant** está habilitado.
- **Una expresión crontab inválida se ignora** — el `crontab` de una consulta personalizada debe tener cinco campos. Una expresión inválida produce un aviso y la consulta se omite.
- **El modo thick no arranca** — **Client path** debe apuntar a las librerías del Oracle Instant Client instaladas en el servidor de Discovery.

## Referencia

### Parámetros de la tarea

#### Oracle Base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|---------|-------|
| Oracle target strings | `_dbstrings_` | textarea | — | Obligatorio. Separados por comas o uno por línea. `#` comenta una línea. Cada entrada crea un agente. Consulte [Cadenas objetivo](#cadenas-objetivo) |
| User | `_dbuser_` | string | — | Obligatorio. Usuario de conexión |
| Password | `_dbpass_` | password | — | Obligatorio. Contraseña de conexión |
| Thick mode | `_thickMode_` | checkbox | desactivado | Usa el Oracle Instant Client en lugar del modo de controlador por defecto |
| Client path | `_clientPath_` | string | — | Visible cuando **Thick mode** está habilitado. Ruta a las librerías del Oracle Instant Client |
| Multitenant: Discover and monitor PDBs within a CDB | `_multiTenant_` | checkbox | desactivado | Descubre PDB en arquitecturas multitenant; aviso inocuo en no CDB |
| Create agent per PDB | `_agentPerPdb_` | checkbox | desactivado | Visible cuando **Multitenant** está habilitado. Un agente por PDB en lugar de módulos en el agente contenedor |
| Enable entities file re-scan interval | `_enableEntitiesInterval_` | checkbox | desactivado | Visible cuando **Multitenant** está habilitado. Refresca periódicamente la lista de PDB descubiertas |
| Re-scan entities file interval | `_entitiesInterval_` | select | `86400` | Visible cuando **Enable entities file re-scan interval** está habilitado. Intervalo de refresco, en los intervalos que ofrece el selector |

#### Oracle Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|---------|-------|
| Max threads | `_threads_` | number | `1` | Hilos de monitorización concurrentes |
| Target agent | `_engineAgent_` | textarea | — | Nombres de agente, emparejados por posición con las cadenas objetivo. En blanco usa la cadena objetivo |
| Custom module prefix | `_prefixModuleName_` | string | — | Se antepone a todos los nombres de módulo generados |
| Check engine uptime | `_checkUptime_` | checkbox | activado | Crea el módulo de detección de reinicio |
| Retrieve query statistics | `_queryStats_` | checkbox | desactivado | Crea los módulos `queries:` |
| Analyze connections | `_checkConnections_` | checkbox | activado | Crea el módulo de uso de sesiones |
| Calculate fragmentation ratio | `_checkFragmentation_` | checkbox | activado | Crea el módulo de ratio de fragmentación |
| Monitor tablespaces | `_checkTablespaces_` | checkbox | activado | Crea los módulos de tablespace libre y estado |
| Retrieve cache statistics | `_checkCache_` | checkbox | activado | Crea los módulos de ratio de acierto de caché |
| Execute custom queries | `_executeCustomQueries_` | checkbox | activado | Habilita el bloque de consultas personalizadas |
| Custom queries | `_customQueries_` | textarea | — | Visible cuando **Execute custom queries** está habilitado. Consulte [Referencia de consultas personalizadas](#referencia-de-consultas-personalizadas) |
| Define tresholds | `_configTresholds_` | textarea | — | Visible siempre. Consulte [Umbrales](#umbrales) |

### Cadenas objetivo

El campo **Oracle target strings** acepta un objetivo por línea o separados por comas. Las líneas en blanco y las que empiezan por `#` se ignoran. Cada objetivo puede usar cualquiera de estos formatos:

```
HOST
HOST/SID
HOST:PORT
HOST:PORT/SID
HOST:PORT/SERVICE_NAME
dsn=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=<HOST>)(PORT=1521))(CONNECT_DATA=(SID=<SID>)))
```

Cuando se omite el puerto, se usa `1521`. Un descriptor DSN puede escribirse con o sin el prefijo `dsn=` (la comparación no distingue mayúsculas y minúsculas), y puede describir una configuración de failover con varias direcciones:

```
dsn=(DESCRIPTION=(FAILOVER=ON)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=<HOST_1>)(PORT=1521))(ADDRESS=(PROTOCOL=TCP)(HOST=<HOST_2>)(PORT=1521)))(CONNECT_DATA=(SID=<SID>)))
```

En un objetivo DSN, el nombre del agente no es el descriptor en bruto: el plugin construye una etiqueta legible con el primer host, puerto y servicio (`Oracle <HOST>:<PORT>/<SERVICE>`), y añade un hash corto cuando el descriptor contiene varias direcciones o servicios.

Cuando el objetivo es un contenedor multitenant y **Multitenant** está habilitado, se puede añadir un filtro de PDB con `|`:

```
HOST:PORT/SERVICE_NAME|PDB1
HOST:PORT/SERVICE_NAME|PDB1;PDB2
```

Sin filtro, se monitorizan todas las PDB elegibles.

### Archivo de configuración

Una tarea de Discovery construye este archivo a partir de sus propios campos. Una ejecución manual lo proporciona con `--conf`.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `agents_group_id` | `10` | Id de grupo asignado a los agentes generados |
| `interval` | `300` | Intervalo del agente y de los módulos, en segundos |
| `user` | Vacío | Usuario de conexión. Obligatorio |
| `password` | Vacío | Contraseña de conexión. Obligatoria |
| `thick_mode` | `0` | `1` habilita el modo thick |
| `client_path` | Vacío | Ruta a las librerías del Oracle Instant Client; se usa con el modo thick |
| `threads` | `1` | Número de hilos de monitorización concurrentes |
| `modules_prefix` | Vacío | Prefijo de los nombres de módulo generados |
| `multitenant` | `0` | `1` descubre y monitoriza PDB |
| `agent_per_pdb` | `0` | `1` crea un agente por PDB; requiere `multitenant=1` |
| `execute_custom_queries` | `1` | `1` ejecuta las consultas personalizadas |
| `analyze_connections` | `1` | `1` crea el módulo de uso de sesiones |
| `engine_uptime` | `1` | `1` crea el módulo de detección de reinicio |
| `query_stats` | `1` | `1` crea los módulos de estadísticas de consultas |
| `cache_stats` | `1` | `1` crea los módulos de ratio de acierto de caché |
| `fragmentation_ratio` | `1` | `1` crea el módulo de ratio de fragmentación |
| `check_tablescpaces` | `1` | `1` crea los módulos de tablespace (la clave conserva esta escritura) |
| `entities_list` | Archivo temporal de la tarea | Ruta del archivo donde se guardan las PDB descubiertas |
| `enable_entities_interval` | `0` | `1` habilita el reescaneo de la lista de PDB |
| `entities_interval` | `86400` | Intervalo de reescaneo, en segundos |
| `cron_state_dir` | Archivo temporal de la tarea | Directorio donde se guarda la última ejecución correcta de las consultas personalizadas programadas |

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

El archivo de configuración y las listas de objetivos contienen la contraseña de la base de datos en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalos fuera de directorios compartidos, registros y control de versiones.

### Ejecución por línea de comandos

El plugin puede ejecutarse a mano, que es la forma más rápida de confirmar un objetivo y sus credenciales antes de integrarlo en una tarea.

```bash
./pandora_oracle \
    --conf <PATH_TO_CONFIG> \
    --target_databases <PATH_TO_TARGETS> \
    [ --target_agents <PATH_TO_AGENT_NAMES> ] \
    [ --custom_queries <PATH_TO_CUSTOM_QUERIES> ]
```

| Parámetro | Descripción |
| --- | --- |
| `--conf` | Ruta al archivo de configuración |
| `--target_databases` | Ruta al archivo que contiene las bases de datos objetivo |
| `--target_agents` | Ruta al archivo que contiene los nombres de agente, emparejados por posición con los objetivos |
| `--custom_queries` | Ruta al archivo que contiene las consultas personalizadas |

La ejecución devuelve un resumen JSON de la ejecución. Los datos recogidos se exponen en el campo `monitoring_data` del resumen para que los consuma el servidor de Discovery.

### Referencia de consultas personalizadas

Cada consulta personalizada es un bloque delimitado por `check_begin` y `check_end`. Solo se permiten sentencias `SELECT`.

| Clave | Descripción |
| --- | --- |
| `name` | Nombre del módulo. Obligatorio |
| `description` | Descripción del módulo |
| `target` | Consulta SQL a ejecutar. Obligatoria. Solo se aceptan sentencias `SELECT` |
| `target_databases` | Cadenas objetivo (o nombres de PDB) separados por comas a los que se aplica la consulta. `all` o vacío la aplica en todas partes |
| `target_scope` | `cdb`, `pdb` o `all`. Vacío o `all` la aplica a ambos ámbitos. `pdb` requiere monitorización multitenant |
| `operation` | `value` devuelve un único valor; `full` devuelve todas las filas como una cadena. Vacío se comporta como `full` |
| `datatype` | `generic_data`, `generic_data_string` o `generic_proc`. Una operación `full` se fuerza a `generic_data_string` |
| `min_warning`, `max_warning` | Umbrales de aviso |
| `min_critical`, `max_critical` | Umbrales críticos |
| `warning_inverse`, `critical_inverse` | Poner a `1` para invertir el intervalo del umbral correspondiente |
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

La consola incluye una guía comentada del campo y un conjunto de consultas de ejemplo como contenido por defecto del área de texto **Custom queries**.

### Umbrales

El campo **Define tresholds** aplica umbrales a los módulos generados por nombre de módulo, excepto a los módulos de consultas personalizadas. Una definición por línea, con una expresión regular que coincide con el nombre del módulo y los umbrales separados por `|`:

```
<REGEX> = <umbral>|<umbral>|...
```

Ejemplo:

```
^tablespace = min_warning 10|max_warning 20|min_critical 0|max_critical 10
```

### Módulos generados

Todos los nombres de módulo llevan el **Custom module prefix** cuando se define uno. Los módulos creados para una PDB conservan el prefijo del contenedor y añaden un segmento `PDB <nombre pdb> `.

#### Agente contenedor

| Módulo | Tipo | Grupo | Habilitado por |
|--------|------|-------|------------|
| `<prefijo>Oracle connection` | `generic_proc` | Disponibilidad | Siempre |
| `<prefijo>restart detection` | `generic_proc` | Uptime | Check engine uptime |
| `<prefijo>queries: select` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefijo>queries: insert` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefijo>queries: delete` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefijo>queries: update` | `generic_data` | Estadísticas de consultas | Retrieve query statistics |
| `<prefijo>tablespace <nombre> free` | `generic_data` | Tablespaces | Monitor tablespaces |
| `<prefijo>tablespace <nombre> status` | `generic_proc` | Tablespaces | Monitor tablespaces |
| `<prefijo>session usage` | `generic_data` | Conexiones | Analyze connections |
| `<prefijo>fragmentation ratio` | `generic_data` | Fragmentación | Calculate fragmentation ratio |
| `<prefijo>cache hit ratio (dictionary)` | `generic_data` | Caché | Retrieve cache statistics |
| `<prefijo>cache hit ratio (library)` | `generic_data` | Caché | Retrieve cache statistics |
| `<prefijo>cache hit ratio (buffer)` | `generic_data` | Caché | Retrieve cache statistics |
| `<prefijo><nombre de consulta>` | Según la consulta | Consultas personalizadas | Execute custom queries |

Los módulos de ratio de acierto de caché llevan umbrales por defecto:

| Módulo | `max_warning` | `max_critical` |
|--------|---------------|----------------|
| `cache hit ratio (dictionary)` | `98` | `40` |
| `cache hit ratio (library)` | `98` | `40` |
| `cache hit ratio (buffer)` | `89` | `40` |

#### Módulos de PDB (Create agent per PDB deshabilitado)

Los mismos módulos que el agente contenedor, con `PDB <nombre pdb> ` insertado tras el prefijo personalizado, por ejemplo `<prefijo>PDB <nombre pdb> tablespace <nombre> free`.

#### Agente de PDB (Create agent per PDB habilitado)

Cada agente de PDB se llama `<agente contenedor> - PDB <nombre pdb>`. Contiene:

- `<prefijo>Oracle PDB <nombre pdb> connection` (disponibilidad)
- Todos los grupos de módulos habilitados, con el prefijo `PDB <nombre pdb> `
- Las consultas personalizadas cuyo ámbito se aplica a las PDB

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la aplicación | `pandorafms.oracle` |
| Versión del plugin | `1.12` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
| Disponibilidad | Marketplace de Pandora FMS (`pandorafms.oracle`) |
