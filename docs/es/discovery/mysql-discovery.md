# MySQL Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de MySQL se conecta a instancias y bases de datos de MySQL y convierte su estado y su rendimiento en agentes y módulos de Pandora FMS. Lee una lista de instancias objetivo, se conecta con un usuario de MySQL y recoge métricas del motor mediante `SHOW GLOBAL STATUS`, `SHOW VARIABLES` y las tablas de `information_schema`.

Una tarea de Discovery crea un agente por instancia objetivo. Cuando **Scan databases** está habilitado recoge también métricas por base de datos, y cuando **Create agent per database** está habilitado crea un agente por base de datos descubierta. Se pueden definir consultas personalizadas para añadir un módulo por consulta y base de datos.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.5` (`pandorafms.mysql`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| Una instancia de MySQL alcanzable | `Requerido` | El plugin establece conexiones remotas con cada instancia monitorizada. Prerrequisito, no una declaración de compatibilidad. |
| Un usuario de MySQL con **SELECT** sobre las tablas de las bases de datos y sobre las tablas de `INFORMATION_SCHEMA` | `Requerido` | Necesario para leer las métricas del motor y por base de datos. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a MySQL](#preparar-el-acceso-a-mysql). |
| Un usuario de MySQL con **SHOW STATUS** y **SHOW VARIABLES** | `Requerido` | Necesario para leer el estado y las variables de configuración del servidor. Prerrequisito, no una declaración de compatibilidad. |
| Una versión concreta de MySQL | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión concreta de MySQL. |
| Una versión concreta de Pandora FMS | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión de consola o de servidor. |
| Un sistema operativo concreto del host | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con sistemas operativos para la máquina que ejecuta el plugin. |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Conectividad** entre el servidor de Pandora FMS y cada instancia de MySQL (puerto por defecto `3306`).
3. **Un usuario de MySQL** con los permisos necesarios. Consulte [Preparar el acceso a MySQL](#preparar-el-acceso-a-mysql).
4. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados, tomados de la tarea de Discovery.

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) con sus dependencias de Python empaquetadas, por lo que no es necesario instalar librerías de Python adicionales en el servidor de Discovery.

### Preparar el acceso a MySQL

El usuario usado por la tarea debe alcanzar cada instancia por red y disponer de los permisos que necesita el monitor. Según los prerrequisitos oficiales:

- **SELECT** sobre las tablas de las bases de datos.
- **SELECT** sobre las tablas de `INFORMATION_SCHEMA`.
- **SHOW STATUS** para consultar el estado del servidor.
- **SHOW VARIABLES** para acceder a las variables de configuración del servidor.

Conceda al usuario únicamente el acceso que exija su política de monitorización; el plugin solo lee y nunca modifica la configuración de MySQL.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager** (la vista *Manage disco packages*). El paquete está disponible en la [librería de Pandora FMS](https://pandorafms.com/library/mysql-discovery/). Una vez cargado, **MySQL** aparece en la categoría **Applications** del asistente de Discovery.

![Vista Manage disco packages con la aplicación de Discovery de MySQL cargada.](../assets/images/discovery/mysql-discovery/disco-packages.png)

![Vista Applications de Discovery con el plugin MySQL disponible.](../assets/images/discovery/mysql-discovery/applications-menu.png)

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → MySQL**. El primer paso genérico define la tarea; el paquete añade **MySQL Base** y **MySQL Detailed**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El ID del grupo y el intervalo se pasan al plugin y se aplican a todos los agentes generados.

**Paso 2 — MySQL Base.** A qué conectarse y cómo:

- **MySQL target strings** es la lista de instancias a monitorizar, separadas por comas o una por línea. Cada objetivo es `SERVER:PORT` o `SERVER`; el puerto por defecto es `3306`. Las líneas que empiezan por `#` son comentarios.
- **User** y **Password** son el usuario de MySQL usado para conectarse.

![Paso Base de la tarea de Discovery de MySQL: target strings, User y Password.](../assets/images/discovery/mysql-discovery/base-step.png)

**Paso 3 — MySQL Detailed.** Ejecución, distribución de agentes y qué métricas se recogen:

- **Max threads** reparte los objetivos entre varios trabajadores en paralelo.
- **Target agent** define los nombres de agente de los objetivos, en la misma posición que la lista de objetivos; una entrada en blanco usa la dirección IP o el FQDN del servidor.
- **Custom module prefix** se antepone a todos los nombres de módulo generados.
- **Scan databases** recoge las métricas por base de datos de cada instancia, y **Create agent per database** crea un agente por base de datos, con **Custom database agent prefix** para nombrarlos.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos.
- **Check engine uptime**, **Retrieve query statistics**, **Analyze connections**, **Retrieve InnoDB statistics** y **Retrieve cache statistics** seleccionan los grupos de métricas del motor recogidos.
- **Execute custom queries** y **Custom queries** definen las consultas personalizadas.

![Paso Detailed de la tarea de Discovery de MySQL.](../assets/images/discovery/mysql-discovery/detailed-step.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de **Total agents**, **Target agents**, **Databases agents**, **Targets up** y **Targets down**. Targets up son las instancias a las que el plugin logró conectarse.

2. **Los agentes.** Aparece un agente por instancia objetivo alcanzable, con el nombre de la lista **Target agent** o la dirección del servidor. Con **Create agent per database**, aparece un agente por base de datos descubierta.

3. **Los módulos del motor.** Una instancia alcanzable lleva sus módulos de conexión, tiempo de actividad, consultas, conexiones, InnoDB y caché según los conmutadores habilitados.

4. **Los módulos de base de datos.** Con **Scan databases** habilitado, cada base de datos lleva sus módulos de disponibilidad, fragmentación, tamaño y consultas personalizadas.

Los objetivos a los que no se puede llegar se cuentan en **Targets down** y no generan agentes.

![Resumen de ejecución de una tarea de Discovery de MySQL.](../assets/images/discovery/mysql-discovery/task-summary.png)

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por instancia objetivo por defecto. El nombre del agente es el valor de la lista **Target agent** que coincide con la posición del objetivo, o la dirección del servidor cuando no se indica ninguno. Cada agente generado informa de `MySQL` como sistema operativo, su `os_version` es el valor devuelto por `SELECT @@VERSION` (o `Discovery` cuando no se puede leer), su `address` es el host de la instancia, y pertenece al grupo de la tarea (por ID) con el intervalo de la tarea. Con **Agent autodisable mode** habilitado los agentes se crean en el modo `2` de Pandora FMS.

Con **Create agent per database**, el plugin crea además un agente por base de datos, llamado `<Custom database agent prefix><agente objetivo> <nombre de base de datos>`, y los cuenta en **Databases agents**. Esos agentes declaran al agente objetivo como padre.

Las bases de datos a monitorizar se recogen de `SHOW DATABASES` cuando **Scan databases** está habilitado; las bases de datos del sistema `mysql`, `information_schema`, `performance_schema` y `sys` se omiten. Las métricas del motor siempre van al agente objetivo, y las métricas por base de datos van a los agentes de base de datos cuando **Create agent per database** está habilitado, o al agente objetivo en caso contrario.

### Módulos por agente

| Agente | Se crea cuando | Módulos que lleva |
| --- | --- | --- |
| Agente objetivo | Una instancia objetivo es alcanzable | `MySQL connection`, los módulos del motor habilitados por los conmutadores y los módulos por base de datos cuando **Scan databases** está habilitado sin **Create agent per database** |
| Agente de base de datos | **Create agent per database** habilitado y una base de datos descubierta | `<base de datos> availability`, `<base de datos> fragmentation ratio`, `<base de datos> size` y los módulos de consultas personalizadas |

Los nombres de módulo son `<Custom module prefix>` más el nombre del módulo; los módulos de base de datos incluyen también el nombre de la base de datos. El inventario exhaustivo de módulos y el conmutador que habilita cada grupo están en [Módulos y agentes generados](#modulos-y-agentes-generados).

## Operación

### Ejecución manual

El plugin puede ejecutarse fuera de Discovery, desde un agente de Pandora FMS o directamente desde la línea de comandos, con un archivo de configuración y los archivos de objetivos, agentes y consultas personalizadas creados manualmente:

```bash
./pandora_mysql --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
```

Solo `--conf` y `--target_databases` son obligatorios; `--target_agents` y `--custom_queries` son opcionales. El plugin se conecta a cada objetivo en paralelo según **Max threads** y produce los agentes y módulos en su salida JSON de Discovery.

El archivo de configuración y las listas de objetivos contienen la contraseña de MySQL en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalos fuera de directorios compartidos, registros y control de versiones. Seguir el flujo de Discovery para las ejecuciones de tarea significa que la consola construye estos archivos por usted.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente y el objetivo se informa como **Targets down** | Confirme que la instancia es alcanzable desde el servidor de Pandora FMS por su puerto (por defecto `3306`), que el servicio de MySQL está en marcha y que **User** y **Password** son correctos. |
| Faltan módulos del motor y la información de ejecución registra errores de recuperación | El usuario necesita **SHOW STATUS** y **SHOW VARIABLES** para las métricas del motor, y **SELECT** sobre `INFORMATION_SCHEMA` para las métricas por base de datos. Conceda esos permisos. |
| Faltan módulos de base de datos | Habilite **Scan databases**. Las bases de datos del sistema `mysql`, `information_schema`, `performance_schema` y `sys` nunca se monitorizan. |
| No se crean agentes de base de datos | Habilite **Create agent per database**. Sin ello, los módulos de base de datos se colocan en el agente objetivo. |
| Faltan módulos de consultas personalizadas | La consulta debe estar entre `check_begin` y `check_end`, ser un `SELECT`, y el usuario necesita **SELECT** sobre las tablas referenciadas. Compruebe la expresión crontab si la consulta está programada. |
| Faltan módulos esperados | Revise los conmutadores del paso **Detailed**: un grupo deshabilitado no produce módulos. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en dos pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### MySQL Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| MySQL target strings | `_dbstrings_` | textarea | — | Lista de instancias objetivo. Obligatorio |
| User | `_dbuser_` | string | — | Usuario de MySQL. Obligatorio |
| Password | `_dbpass_` | password | — | Contraseña de MySQL. Obligatorio |

#### MySQL Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `1` | Trabajadores que reparten los objetivos |
| Target agent | `_engineAgent_` | textarea | — | Nombres de agente de los objetivos, en la posición de la lista; en blanco usa la dirección del servidor |
| Custom module prefix | `_prefixModuleName_` | string | — | Prefijo antepuesto a todos los nombres de módulo |
| Scan databases | `_scanDatabases_` | checkbox | off | Recoge las métricas por base de datos de cada instancia |
| Create agent per database | `_agentPerDatabase_` | checkbox | off | Crea un agente por base de datos |
| Custom database agent prefix | `_prefixAgent_` | string | — | Prefijo de los agentes de base de datos. Solo se muestra cuando **Create agent per database** está habilitado |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos |
| Check engine uptime | `_checkUptime_` | checkbox | on | Detección de reinicio del servidor |
| Retrieve query statistics | `_queryStats_` | checkbox | on | Contadores y tasas de consultas |
| Analyze connections | `_checkConnections_` | checkbox | on | Conexiones actuales, ratio de conexión y conexiones abortadas |
| Retrieve InnoDB statistics | `_checkInnodb_` | checkbox | on | Actividad del búfer y del disco de InnoDB |
| Retrieve cache statistics | `_checkCache_` | checkbox | on | Estado de la caché de consultas y ratio de aciertos |
| Execute custom queries | `_executeCustomQueries_` | checkbox | on | Habilita las consultas personalizadas |
| Custom queries | `_customQueries_` | textarea | — | Definición de las consultas personalizadas. Solo se muestra cuando **Execute custom queries** está habilitado |

### Archivo de configuración

La tarea de Discovery construye un archivo `--conf` temporal a partir de sus propios campos. Una ejecución manual lo suministra directamente. El archivo tiene una sección `[CONF]`; el plugin la lee sin cabecera de sección.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `agents_group_id` | `10` | ID del grupo donde se crean los agentes |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes |
| `user` | Vacío | Usuario de conexión. Obligatorio |
| `password` | Vacío | Contraseña del usuario. Obligatorio |
| `threads` | `1` | Número de trabajadores en paralelo |
| `modules_prefix` | Vacío | Prefijo de los nombres de módulo |
| `execute_custom_queries` | `1` | Habilita las consultas personalizadas |
| `analyze_connections` | `1` | Módulos de conexión |
| `scan_databases` | `0` | Recoge las métricas por base de datos |
| `agent_per_database` | `0` | Crea un agente por base de datos |
| `agent_autodisable` | `0` | Crea los agentes en el modo `2` de Pandora FMS cuando está habilitado |
| `db_agent_prefix` | Vacío | Prefijo de los agentes de base de datos |
| `innodb_stats` | `1` | Estadísticas de InnoDB |
| `engine_uptime` | `1` | Tiempo de actividad del motor |
| `query_stats` | `1` | Estadísticas de consultas |
| `cache_stats` | `1` | Estadísticas de caché |
| `cron_state_dir` | Vacío | Carpeta para el estado crontab de las consultas personalizadas; se deriva de la ruta temporal de la tarea |

El archivo `--conf` y las listas de objetivos contienen la contraseña de MySQL en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalos fuera de directorios compartidos, registros y control de versiones.

### Bases de datos objetivo

El archivo `--target_databases` contiene una o más cadenas objetivo, separadas por comas o una por línea. Las líneas que empiezan por `#` y las líneas en blanco se ignoran. Cada objetivo es `SERVER:PORT` o `SERVER`; el puerto por defecto es `3306`.

```text
172.17.0.4:3306
172.17.0.5
```

### Agentes objetivo

El archivo opcional `--target_agents` contiene un nombre de agente por objetivo, separados por comas o una por línea. La posición de cada nombre coincide con la posición del objetivo correspondiente en la lista de objetivos; las líneas en blanco se ignoran. Una entrada en blanco deja el agente con la dirección IP o el FQDN del servidor.

### Ejecución en línea de comandos

El plugin acepta un archivo de configuración, un archivo de bases de datos objetivo, un archivo opcional de agentes objetivo y un archivo opcional de consultas personalizadas:

```bash
./pandora_mysql --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
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
user=<MYSQL_USER>
password=<MYSQL_PASSWORD>
threads=1
modules_prefix=
execute_custom_queries=1
engine_uptime=1
query_stats=1
analyze_connections=1
innodb_stats=1
cache_stats=1
scan_databases=1
agent_per_database=0
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
| `target_databases` | Bases de datos donde se crea el módulo; `all` o vacío aplica a todas |

Los campos `target` y `name` admiten la palabra reservada `$__self_dbname`, que se reemplaza por el nombre de la base de datos que se está analizando. El campo `crontab` sigue el formato estándar de 5 campos y admite `*`, valores exactos, rangos, pasos y listas; en la primera ejecución tras habilitar una consulta programada solo se recoge una ocurrencia dentro del intervalo actual.

```text
check_begin
name ConnectionCount
description Number of connections
operation value
datatype generic_data
min_warning 10
target SELECT COUNT(*) AS ConnectionCount FROM $__self_dbname.processlist
target_databases all
check_end
```

### Módulos y agentes generados

Los nombres de módulo son `[<Custom module prefix>]<nombre de módulo>`, y los módulos de base de datos incluyen también el nombre de la base de datos.

**Agente objetivo** (uno por instancia alcanzable)

Siempre se crea:

- `MySQL connection`: `generic_proc`, `1` cuando la instancia es alcanzable, `0` en caso contrario.

Se crean cuando el conmutador correspondiente está habilitado:

- **Check engine uptime**: `restart detection` (`generic_proc`, `0` cuando se detecta un reinicio, `1` en caso contrario). La descripción lleva el tiempo de actividad.
- **Retrieve query statistics**: `queries` (`generic_data_inc_abs`, total), `query rate` (`generic_data_inc`), `query select`, `query update`, `query delete`, `query insert` (`generic_data_inc_abs`).
- **Analyze connections**: `current connections` (`generic_data`, aviso al 90% y crítico al 98% de `max_connections`), `connections ratio` (`generic_data`, unidad `%`, aviso en `85` y crítico en `90`), `aborted connections` (`generic_data_inc_abs`).
- **Retrieve InnoDB statistics**: `Innodb buffer pool pages total` (`generic_data`), `Innodb buffer pool read requests`, `Innodb buffer pool write requests` (`generic_data_inc_abs`), `Innodb disk reads`, `Innodb disk writes` (`generic_data_inc_abs`), `Innodb disk data read`, `Innodb disk data written` (`generic_data_inc_abs`, unidad `MB`).
- **Retrieve cache statistics**: `query cache enabled` (`generic_proc`, `1` cuando la caché de consultas está habilitada), `query hit ratio` (`generic_data`, unidad `%`, creado solo cuando la caché de consultas está habilitada).

**Módulos de base de datos** (en el agente objetivo o en el agente de base de datos, creados cuando **Scan databases** está habilitado, para cada base de datos distinta de las del sistema)

- `<base de datos> availability`: `generic_proc`, `1`.
- `<base de datos> fragmentation ratio`: `generic_data`, unidad `%`.
- `<base de datos> size`: `generic_data`, unidad `MB`.
- Los módulos de consultas personalizadas que apuntan a la base de datos.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.mysql` |
| Versión del plugin | `1.5` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |