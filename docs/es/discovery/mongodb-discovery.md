# MongoDB Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de MongoDB se conecta a despliegues y bases de datos de MongoDB y convierte su estado y su rendimiento en agentes y módulos de Pandora FMS. Lee una lista de objetivos dados como URI de conexión, se autentica con el usuario embebido en cada URI y recoge métricas del motor mediante los comandos `serverStatus`, `dbStats` y otros.

Una tarea de Discovery crea un agente por objetivo. Cuando **Scan databases** está habilitado recoge también métricas por base de datos, y cuando **Create agent per database** está habilitado crea un agente por base de datos descubierta. Se pueden definir consultas personalizadas para añadir un módulo por consulta y base de datos.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.6` (`pandorafms.mongodb`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| Un despliegue de MongoDB alcanzable | `Requerido` | El plugin establece conexiones remotas con cada objetivo mediante su URI de conexión. Prerrequisito, no una declaración de compatibilidad. |
| Un usuario de MongoDB con el rol `read` o `dbAdmin` sobre las bases de datos monitorizadas | `Requerido` | Necesario para los comandos de nivel de base de datos. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a MongoDB](#preparar-el-acceso-a-mongodb). |
| Un usuario de MongoDB con el rol `clusterMonitor` o `clusterAdmin` | `Requerido` | Necesario para las estadísticas del servidor. Prerrequisito, no una declaración de compatibilidad. |
| Una versión concreta de MongoDB | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión concreta de MongoDB. |
| Una versión concreta de Pandora FMS | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión de consola o de servidor. |
| Un sistema operativo concreto del host | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con sistemas operativos para la máquina que ejecuta el plugin. |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Conectividad** entre el servidor de Pandora FMS y cada despliegue de MongoDB (puerto por defecto `27017`).
3. **Un usuario de MongoDB** con los roles necesarios. Consulte [Preparar el acceso a MongoDB](#preparar-el-acceso-a-mongodb).
4. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados, tomados de la tarea de Discovery.

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) con sus dependencias de Python empaquetadas, por lo que no es necesario instalar librerías de Python adicionales en el servidor de Discovery.

### Preparar el acceso a MongoDB

El usuario usado por la tarea debe alcanzar cada despliegue por red y disponer de los roles que necesita el monitor. Según los prerrequisitos oficiales:

- **Para bases de datos**: el rol `read` o `dbAdmin` sobre las bases de datos que se vayan a monitorizar.
- **Para estadísticas del servidor**: el rol `clusterMonitor` o `clusterAdmin`.

Conceda al usuario únicamente el acceso que exija su política de monitorización; el plugin solo lee y nunca modifica los datos ni la configuración de MongoDB.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager** (la vista *Manage disco packages*). El paquete está disponible en la [librería de Pandora FMS](https://pandorafms.com/library/mongodb-discovery/). Una vez cargado, **MongoDB** aparece en la categoría **Applications** del asistente de Discovery.

![Vista Manage disco packages con la aplicación de Discovery de MongoDB cargada.](../assets/images/discovery/mongodb-discovery/disco-packages.png)

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → MongoDB**. El primer paso genérico define la tarea; el paquete añade **MongoDB Base**, **MongoDB Detailed** y **MongoDB custom**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El ID del grupo y el intervalo se pasan al plugin y se aplican a todos los agentes generados.

**Paso 2 — MongoDB Base.** Los objetivos a los que conectarse:

- **MongoDB target strings** es la lista de instancias a monitorizar, separadas por comas o una por línea. Cada objetivo es una URI de conexión de MongoDB, por ejemplo `mongodb://172.17.0.2:27017` o `mongodb+srv://monitor.user:password@cluster.example.com/my_db`. Las líneas que empiezan por `#` son comentarios.

![Paso Base de la tarea de Discovery de MongoDB: MongoDB target strings.](../assets/images/discovery/mongodb-discovery/base-step.png)

**Paso 3 — MongoDB Detailed.** Ejecución, distribución de agentes y qué métricas se recogen:

- **Max threads** reparte los objetivos entre varios trabajadores en paralelo.
- **Target agents** define los nombres de agente de los objetivos, en la misma posición que la lista de objetivos; una entrada en blanco usa la cadena del objetivo.
- **Use prefix for modules** y **Custom module prefix** anteponen un prefijo a todos los nombres de módulo generados.
- **Scan databases** recoge las métricas por base de datos de cada objetivo, y **Create agent per database** crea un agente por base de datos, con **Custom database agent prefix** para nombrarlos.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos.
- **Check engine uptime**, **Retrieve query statistics**, **Analyze connections**, **Retrieve latency statistics** y **Retrieve network statistics** seleccionan los grupos de métricas del motor recogidos.

![Paso Detailed de la tarea de Discovery de MongoDB.](../assets/images/discovery/mongodb-discovery/detailed-step.png)

**Paso 4 — MongoDB custom.** Las consultas personalizadas:

- **Execute custom queries** habilita las consultas personalizadas, y **Custom queries** las define.

![Paso Custom de la tarea de Discovery de MongoDB.](../assets/images/discovery/mongodb-discovery/custom-step.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de **Total agents**, **Targets up** y **Targets down**. Targets up son los objetivos a los que el plugin logró conectarse.

2. **Los agentes.** Aparece un agente por objetivo alcanzable, con el nombre de la lista **Target agents** o la cadena del objetivo. Con **Create agent per database**, aparece un agente por base de datos descubierta.

3. **Los módulos del motor.** Un objetivo alcanzable lleva sus módulos de conexión, tiempo de actividad, consultas, conexiones, latencia y red según los conmutadores habilitados.

4. **Los módulos de base de datos.** Con **Scan databases** habilitado, cada base de datos lleva sus módulos de colecciones, índices, tamaño, estado y consultas personalizadas.

Los objetivos a los que no se puede llegar se cuentan en **Targets down** y no generan agentes.

![Resumen de ejecución de una tarea de Discovery de MongoDB.](../assets/images/discovery/mongodb-discovery/task-summary.png)

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por objetivo por defecto. El nombre del agente es el valor de la lista **Target agents** que coincide con la posición del objetivo, o la cadena del objetivo cuando no se indica ninguno. Cada agente generado informa de `MONGODB` como sistema operativo, su `os_version` es la versión de MongoDB devuelta por la información del servidor (o `Discovery` cuando no se puede leer), y pertenece al grupo de la tarea (por ID) con el intervalo de la tarea. Con **Agent autodisable mode** habilitado los agentes se crean en el modo `2` de Pandora FMS. Los agentes generados se devuelven en la salida JSON del plugin.

Con **Create agent per database**, el plugin crea además un agente por base de datos, llamado `<Custom database agent prefix><agente objetivo> <nombre de base de datos>`, y los cuenta en **Total agents**.

Las bases de datos a monitorizar se recogen del despliegue cuando **Scan databases** está habilitado. Cuando un objetivo lista bases de datos tras `|` en su URI, solo se monitorizan esas; añadir `!` a la URI excluye las listadas y monitoriza el resto. Las métricas del motor siempre van al agente objetivo, y las métricas por base de datos van a los agentes de base de datos cuando **Create agent per database** está habilitado, o al agente objetivo en caso contrario.

### Módulos por agente

| Agente | Se crea cuando | Módulos que lleva |
| --- | --- | --- |
| Agente objetivo | Un objetivo es alcanzable | `MONGODB connection`, los módulos del motor habilitados por los conmutadores y los módulos por base de datos cuando **Scan databases** está habilitado sin **Create agent per database** |
| Agente de base de datos | **Create agent per database** habilitado y una base de datos descubierta | Las métricas `<base de datos>` y los módulos de consultas personalizadas |

Los nombres de módulo son `<Custom module prefix>` más el nombre del módulo; los módulos de base de datos incluyen también el nombre de la base de datos. El inventario exhaustivo de módulos y el conmutador que habilita cada grupo están en [Módulos y agentes generados](#modulos-y-agentes-generados).

## Operación

### Ejecución manual

El plugin puede ejecutarse fuera de Discovery, desde un agente de Pandora FMS o directamente desde la línea de comandos, con un archivo de configuración y los archivos de objetivos, agentes y consultas personalizadas creados manualmente:

```bash
./pandora_mongodb --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
```

Solo `--conf` y `--target_databases` son obligatorios; `--target_agents` y `--custom_queries` son opcionales. El plugin se conecta a cada objetivo en paralelo según **Max threads** y produce los agentes y módulos en su salida JSON de Discovery.

La lista de objetivos contiene las URI de conexión, que pueden embeker un nombre de usuario y una contraseña. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalos fuera de directorios compartidos, registros y control de versiones.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente y el objetivo se informa como **Targets down** | Confirme que el despliegue es alcanzable desde el servidor de Pandora FMS por su puerto (por defecto `27017`), que el servicio de MongoDB está en marcha y que la URI de conexión es correcta. |
| Faltan módulos del motor y la información de ejecución registra errores de comando | El usuario necesita el rol `clusterMonitor` o `clusterAdmin` para las estadísticas del servidor (`serverStatus`), y `read` o `dbAdmin` sobre las bases de datos monitorizadas. Conceda esos roles. |
| Faltan módulos de base de datos | Habilite **Scan databases**. Un objetivo sin lista `|` de bases de datos y con **Scan databases** deshabilitado solo produce los módulos del motor. |
| No se crean agentes de base de datos | Habilite **Create agent per database**. Sin ello, los módulos de base de datos se colocan en el agente objetivo. |
| Faltan módulos de consultas personalizadas | La consulta debe estar entre `check_begin` y `check_end`, usar un comando de lectura permitido y ejecutarse con **Scan databases** habilitado. Compruebe la expresión crontab si la consulta está programada. |
| Faltan módulos esperados | Revise los conmutadores del paso **Detailed**: un grupo deshabilitado no produce módulos. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### MongoDB Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| MongoDB target strings | `_dbstrings_` | textarea | — | Lista de URI de conexión de MongoDB. Obligatorio |

#### MongoDB Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `1` | Trabajadores que reparten los objetivos |
| Target agents | `_engineAgent_` | textarea | — | Nombres de agente de los objetivos, en la posición de la lista; en blanco usa la cadena del objetivo |
| Use prefix for modules | `_usePrefixmodule_` | checkbox | off | Habilita el prefijo de módulos |
| Custom module prefix | `_prefixModuleName_` | string | — | Prefijo antepuesto a todos los nombres de módulo. Solo se muestra cuando **Use prefix for modules** está habilitado |
| Scan databases | `_scanDatabases_` | checkbox | off | Recoge las métricas por base de datos de cada objetivo |
| Create agent per database | `_agentPerDatabase_` | checkbox | off | Crea un agente por base de datos |
| Custom database agent prefix | `_prefix_` | string | — | Prefijo de los agentes de base de datos. Solo se muestra cuando **Create agent per database** está habilitado |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos |
| Check engine uptime | `_checkUptime_` | checkbox | on | Tiempo de actividad del servidor |
| Retrieve query statistics | `_queryStats_` | checkbox | on | Contadores de operaciones de consulta |
| Analyze connections | `_checkConnections_` | checkbox | on | Contadores de conexiones |
| Retrieve latency statistics | `_checkLatency_` | checkbox | on | Latencias de operaciones |
| Retrieve network statistics | `_checkNetwork_` | checkbox | on | Contadores de tráfico de red |

#### MongoDB custom

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Execute custom queries | `_executeCustomQueries_` | checkbox | on | Habilita las consultas personalizadas |
| Custom queries | `_customQueries_` | textarea | — | Definición de las consultas personalizadas. Solo se muestra cuando **Execute custom queries** está habilitado |

### Archivo de configuración

La tarea de Discovery construye un archivo `--conf` temporal a partir de sus propios campos. Una ejecución manual lo suministra directamente. El archivo tiene una sección `[CONF]`; el plugin la lee sin cabecera de sección.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `agents_group_id` | `10` | ID del grupo donde se crean los agentes |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes |
| `threads` | `1` | Número de trabajadores en paralelo |
| `modules_prefix` | Vacío | Prefijo de los nombres de módulo |
| `execute_custom_queries` | `1` | Habilita las consultas personalizadas |
| `analyze_connections` | `0` | Contadores de conexiones |
| `engine_uptime` | `0` | Tiempo de actividad del servidor |
| `query_stats` | `0` | Estadísticas de consultas |
| `network` | `0` | Estadísticas de red |
| `latency` | `0` | Estadísticas de latencia |
| `scan_databases` | `0` | Recoge las métricas por base de datos |
| `agent_per_database` | `0` | Crea un agente por base de datos |
| `agent_autodisable` | `0` | Crea los agentes en el modo `2` de Pandora FMS cuando está habilitado |
| `db_agent_prefix` | Vacío | Prefijo de los agentes de base de datos |
| `cron_state_dir` | Vacío | Carpeta para el estado crontab de las consultas personalizadas; se deriva de la ruta temporal de la tarea |

### Bases de datos objetivo

El archivo `--target_databases` contiene una o más URI de conexión de MongoDB, separadas por comas o una por línea. Las líneas que empiezan por `#` y las líneas en blanco se ignoran. Una URI puede incluir una coma dentro de una cadena de conexión de réplica.

```text
mongodb://172.17.0.2:27017
mongodb://monitor.user:s3cur3P@ss@mongo-prod-01.internal.company.com:27017/my_db
```

Para monitorizar bases de datos concretas de un objetivo, añada `|` y separe las bases de datos con `;`:

```text
mongodb://172.17.0.2:27017|my_db;test
```

Para monitorizar todas las bases de datos excepto un conjunto, añada `!` antes de la `|`:

```text
mongodb://172.17.0.2:27017!|my_db;test
```

### Agentes objetivo

El archivo opcional `--target_agents` contiene un nombre de agente por objetivo, separados por comas o una por línea. La posición de cada nombre coincide con la posición del objetivo correspondiente en la lista de objetivos; las líneas en blanco se ignoran. Una entrada en blanco deja el agente con el nombre de la cadena del objetivo.

### Ejecución en línea de comandos

El plugin acepta un archivo de configuración, un archivo de bases de datos objetivo, un archivo opcional de agentes objetivo y un archivo opcional de consultas personalizadas:

```bash
./pandora_mongodb --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
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
threads=1
modules_prefix=
execute_custom_queries=1
engine_uptime=1
query_stats=1
analyze_connections=1
latency=1
network=1
scan_databases=1
agent_per_database=0
```

### Consultas personalizadas

Cada consulta personalizada crea un módulo por agente y base de datos coincidentes y se define entre `check_begin` y `check_end`:

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
| `target` | El comando, uno de `dbStats`, `collStats`, `find`, `count`, `aggregate`, `listCollections` |
| `target_instances` | Objetivos o agentes donde se crea el módulo; `all` o vacío aplica a todos |
| `target_databases` | Bases de datos donde se crea el módulo; `all` o vacío aplica a todas |
| `ignore_databases` | Bases de datos donde no se crea el módulo |

Las consultas personalizadas se ejecutan contra las bases de datos monitorizadas durante el escaneo de bases de datos, por lo que **Scan databases** debe estar habilitado para que se ejecuten. El target admite la palabra reservada `$__self_dbname`, que se reemplaza por el nombre de la base de datos que se está analizando. Los comandos soportados son de solo lectura; `dbStats`, `collStats`, `find`, `count`, `aggregate` y `listCollections` están permitidos, el resto de comandos se rechazan.

```text
check_begin
name Query count
description Number of documents
operation value
datatype generic_data
min_warning 10
target db.coll.count({})
target_databases all
check_end
```

### Módulos y agentes generados

Los nombres de módulo son `[<Custom module prefix>]<nombre de módulo>`, y los módulos de base de datos incluyen también el nombre de la base de datos.

**Agente objetivo** (uno por objetivo alcanzable)

Siempre se crea:

- `MONGODB connection`: `generic_proc`, `1` cuando el objetivo es alcanzable, `0` en caso contrario.

Se crean cuando el conmutador correspondiente está habilitado:

- **Check engine uptime**: `Uptime` (`generic_data`, tiempo de actividad estimado).
- **Retrieve query statistics**: `queries command`, `queries delete`, `queries getmore`, `queries insert`, `queries query`, `queries update` (`generic_data`, contadores de operaciones).
- **Analyze connections**: `connections current`, `connections available`, `connections totalCreated` (`generic_data`).
- **Retrieve latency statistics**: `operationlatencies.reads latency`, `operationlatencies.reads ops`, `operationlatencies.writes latency`, `operationlatencies.writes ops`, `operationlatencies.commands latency`, `operationlatencies.commands ops` (`generic_data`).
- **Retrieve network statistics**: `network bytesIn`, `network bytesOut`, `network numRequests` (`generic_data`).

**Módulos de base de datos** (en el agente objetivo o en el agente de base de datos, creados cuando **Scan databases** está habilitado, para cada base de datos encontrada en el objetivo)

- `<base de datos> collections`: `generic_data`, número de colecciones.
- `<base de datos> indexes`: `generic_data`, número de índices.
- `<base de datos> indexSize`: `generic_data`, tamaño total de todos los índices (bytes).
- `<base de datos> views`: `generic_data`, número de vistas.
- `<base de datos> objects`: `generic_data`, número de documentos.
- `<base de datos> avgObjSize`: `generic_data`, tamaño medio de documento (bytes).
- `<base de datos> dataSize`: `generic_data`, tamaño total de los datos (bytes).
- `<base de datos> storageSize`: `generic_data`, espacio usado en disco (bytes).
- `<base de datos> totalSize`: `generic_data`, suma del tamaño de datos e índices (bytes).
- `<base de datos> fsUsedSize`: `generic_data`, espacio usado en el sistema de archivos (bytes).
- `<base de datos> fsTotalSize`: `generic_data`, tamaño total del sistema de archivos (bytes).
- `<base de datos> status`: `generic_data`, `1` cuando la base de datos responde, `0` en caso contrario.
- Los módulos de consultas personalizadas que coinciden con la base de datos.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.mongodb` |
| Versión del plugin | `1.6` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |