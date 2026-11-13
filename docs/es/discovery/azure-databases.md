# Azure Databases Discovery

*Última actualización del artículo: 2026-11-06.*

## Qué monitoriza

El plugin de Discovery de Azure Databases descubre los servidores de Azure Database for MySQL y Azure Database for MariaDB de una suscripción de Microsoft Azure y convierte su estado y sus métricas de Azure Monitor en agentes y módulos de Pandora FMS: rendimiento de CPU, memoria y almacenamiento, uso de almacenamiento y binlog, conexiones, tráfico, replicación y métricas del motor MySQL/InnoDB.

Por defecto crea **un agente por servidor de base de datos**, llamado `[Agent prefix]Azure Database <servidor>`. También puede consolidar todos los servidores descubiertos en un único **Target agent**, con el nombre del servidor antepuesto a cada nombre de módulo. Cada agente lleva un módulo de disponibilidad, un módulo de servidor en línea y un módulo por grupo de métricas habilitado.

El plugin cubre la familia MySQL solicitada en la petición original:

| Motor | Tipo de recurso de Azure |
| --- | --- |
| MySQL Flexible Server | `Microsoft.DBforMySQL/flexibleServers` |
| MySQL Single Server | `Microsoft.DBforMySQL/servers` |
| MariaDB Server | `Microsoft.DBforMariaDB/servers` |

Azure Database for MySQL y MariaDB no ofrecen motores Oracle, por lo que este plugin no cubre Oracle. El plugin de Discovery de Azure SQL documenta Azure SQL Database por separado.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.azure.database`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Una suscripción de Azure con servidores Azure Database for MySQL o MariaDB | `Requerido` | El plugin descubre y lee servidores de base de datos. Prerrequisito, no una declaración de compatibilidad |
| Una entidad de servicio de Microsoft Entra con permisos de lectura sobre la suscripción o el Resource Group | `Requerido` | El plugin lista servidores y lee sus métricas de Azure Monitor. Normalmente el rol `Reader` es suficiente. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure) |
| Un grupo de agentes de Pandora FMS con ID mayor que `0` | `Requerido` | El grupo `All` tiene ID `0` y no se puede usar |
| Nubes de Azure soberanas o personalizadas | `Sin validar` | Los endpoints son configurables, pero ningún registro de pruebas establece su funcionamiento contra una nube no pública |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga servidores Azure Database for MySQL o MariaDB.
3. **Una credencial de Azure** guardada en el almacén de credenciales de Pandora FMS, o sus valores suministrados directamente para una ejecución manual.
4. **Un grupo de agentes válido** para la tarea. El grupo `All` no es válido, porque su ID es `0`.

El plugin se distribuye como un ejecutable autocontenido: la aplicación Discovery empaquetada incluye `bin/pandora_azure_database`, por lo que no es necesario instalar ningún runtime adicional en el servidor de Pandora FMS ni para una ejecución manual.

### Preparar el acceso a Azure

Cree una entidad de servicio de Microsoft Entra con permisos de solo lectura y asígnele el rol **Reader** sobre la suscripción o el Resource Group que se vaya a descubrir. En la mayoría de entornos `Reader` es suficiente; cuando el acceso se limita a un único Resource Group, configure también el campo **Resource group** en la tarea. La entidad de servicio debe poder:

- Listar los recursos `Microsoft.DBforMySQL/flexibleServers`.
- Listar los recursos `Microsoft.DBforMySQL/servers`.
- Listar los recursos `Microsoft.DBforMariaDB/servers`.
- Leer propiedades del servidor, como estado, versión, SKU y nombre de dominio completo.
- Consultar las métricas de Azure Monitor de cada servidor.

El proveedor de cada motor debe estar registrado en la suscripción. El plugin omite un motor cuyo proveedor no esté registrado y lo informa en la información de la tarea, de modo que el resto de motores se siguen descubriendo.

Guarde el **Client ID**, el **Application secret**, el **Tenant or domain name** y el **Subscription id** de la entidad de servicio como una credencial de Azure en el almacén de credenciales de Pandora FMS, de modo que la tarea haga referencia a la credencial en lugar de transportar el secreto.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Azure Databases** aparece en la categoría **Cloud** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure Databases**. El primer paso genérico del asistente define la tarea; el paquete añade **Azure credentials**, **Database discovery** y **Modules**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo, servidor e intervalo. El grupo debe tener un ID mayor que `0`; `All` no se puede usar. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure credentials.** La credencial y los endpoints de Azure:

- **Azure credentials** selecciona la credencial de Azure guardada. Es obligatoria.
- **API endpoint** y **Login endpoint** sobrescriben los endpoints de Azure Resource Manager y de autenticación de Azure para nubes soberanas o personalizadas. Los valores vacíos usan los endpoints públicos de Azure.

![Paso Azure credentials de la tarea de Discovery de Azure Databases.](../assets/images/discovery/azure-databases/azure-credentials.png)

**Paso 3 — Database discovery.** Qué descubrir y cómo se distribuyen los agentes:

- **Resource group** y **Server name** filtran el descubrimiento. Cada uno acepta varios valores exactos y sin distinguir mayúsculas, separados por `;`. Vacío descubre todo.
- **Discover MySQL servers** incluye los recursos MySQL Flexible Server y MySQL Single Server.
- **Discover MariaDB servers** incluye los recursos Azure Database for MariaDB.
- **Create agent per server** decide la distribución de agentes, y **Target agent** solo se usa cuando está deshabilitado.
- **Agent prefix** y **Module prefix** se anteponen a los nombres de agente y de módulo.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS.
- **Enable entities file re-scan interval** y **Re-scan entities file interval** controlan cuánto tiempo se reutiliza la caché de servidores descubiertos antes de reconstruirse.
- **Request timeout** es el tiempo de espera HTTP de Azure en segundos. El valor mínimo aplicado es `30`.

Al menos una de las opciones **Discover MySQL servers** o **Discover MariaDB servers** debe permanecer habilitada.

![Paso Database discovery de la tarea de Discovery de Azure Databases.](../assets/images/discovery/azure-databases/database-discovery.png)

**Paso 4 — Modules.** Qué familias de métricas se recogen:

- **Performance modules**: CPU, memoria y porcentaje de E/S de almacenamiento.
- **Storage modules**: almacenamiento usado y límite, uso de log del servidor, almacenamiento de copias y, cuando está disponible, almacenamiento de binlog.
- **Connection modules**: conexiones activas, fallidas y, cuando están disponibles, totales y abortadas.
- **Traffic modules**: red de entrada y red de salida.
- **Replication modules**: retraso de replicación y, cuando está disponible, estado de los hilos IO y SQL de la réplica.
- **Engine modules**: consultas, consultas lentas, hilos en ejecución, lecturas y peticiones del buffer pool de InnoDB, interbloqueos y tiempos de espera de bloqueo.

![Paso Modules de la tarea de Discovery de Azure Databases.](../assets/images/discovery/azure-databases/modules.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de `resources_discovered`, `resources_vanished`, `modules` y `errors`. Espere un recurso descubierto por servidor de base de datos y `errors` en `0`.

2. **Los agentes.** Con **Create agent per server** habilitado, aparece un agente por servidor descubierto, llamado `[Agent prefix]Azure Database <servidor>`. Cada uno informa de `Azure` como sistema operativo y hereda el grupo y el intervalo de la tarea.

3. **`Azure Database Connection`** es `1` en todo servidor descubierto, y **`Database online`** es `1` cuando el estado del servidor es `Ready`, `Online` o `Running`.

4. **Los módulos de métricas** de cada familia habilitada. Un servidor solo recibe un módulo cuando Azure expone la métrica y admite la agregación que usa el plugin.

Si no aparece ningún agente, lo primero que hay que revisar son la credencial, sus permisos o los filtros.

![Resumen de ejecución de la tarea de Discovery de Azure Databases.](../assets/images/discovery/azure-databases/task-summary.png)

![Agentes generados por el Discovery de Azure Databases.](../assets/images/discovery/azure-databases/agents.png)

## Interpretar los resultados

### Distribución de agentes

**Con Create agent per server habilitado**, que es el valor por defecto, el plugin crea un agente por servidor, llamado `[Agent prefix]Azure Database <servidor>`, con el FQDN del servidor como dirección y el ID del recurso en la descripción.

**Con él deshabilitado**, todos los módulos van al único **Target agent** y el nombre del servidor se antepone a cada nombre de módulo como `<servidor> <nombre del módulo>`. Esto importa al leer los módulos: en modo consolidado el nombre del módulo identifica el servidor.

Los agentes generados informan de `Azure` como sistema operativo, `os_version` es la edición y versión del motor, heredan el grupo y el intervalo de la tarea, y se crean en el modo `2` de Pandora FMS cuando **Agent autodisable mode** está habilitado, o en el modo `1` cuando está deshabilitado.

### Descubrimiento y filtros

Los filtros **Resource group** y **Server name** usan coincidencias exactas y sin distinguir mayúsculas, no expresiones regulares; separe varios valores con `;`. Las opciones **Discover MySQL servers** y **Discover MariaDB servers** deciden qué tipos de recurso se consultan.

Los servidores descubiertos se conservan en el archivo de entidades. Una entidad guardada que ya no aparece en un escaneo se cuenta en `resources_vanished` y genera solo `Azure Database Connection` con valor `0`, de modo que un servidor eliminado o renombrado queda visible en lugar de desaparecer en silencio. Cuando el intervalo de reescaneo expira, la caché se reconstruye sin comparar con las entidades anteriores.

Si el proveedor de un motor no está registrado en la suscripción, el plugin lo informa en la información de la tarea y continúa con los demás motores en lugar de hacer fallar toda la tarea.

### Qué se crea

| Habilitado por | Qué se obtiene |
| --- | --- |
| Siempre | `Azure Database Connection` y `Database online` |
| Siempre, cuando Azure expone la propiedad | `Public network access` |
| Performance modules | `CPU percent`, `Memory percent`, `Storage IO percent` |
| Storage modules | `Storage used GB`, `Storage used percent`, `Storage limit GB`, `Server log used GB`, `Server log used percent`, `Backup storage used GB`, `Binlog storage used GB` |
| Connection modules | `Active connections`, `Failed connections`, `Total connections`, `Aborted connections` |
| Traffic modules | `Network in MB`, `Network out MB` |
| Replication modules | `Replication lag seconds`, `Replica IO running`, `Replica SQL running` |
| Engine modules | `Queries`, `Slow queries`, `Threads running`, `InnoDB buffer pool reads`, `InnoDB buffer pool read requests`, `Deadlocks`, `Lock timeouts` |

El plugin lee las métricas de Azure Monitor y solo crea un módulo de métrica cuando el servidor expone esa métrica y admite su agregación. El inventario exhaustivo de módulos, unidades y agregaciones está en [Módulos generados](#modulos-generados).

![Módulos generados para un servidor MySQL flexible de Azure Database.](../assets/images/discovery/azure-databases/mysql-modules.png)

La captura muestra un servidor MySQL flexible; los servidores MariaDB exponen el subconjunto de métricas disponible en su motor.

## Solución de problemas

- **La tarea falla por el grupo** — el grupo de agentes debe tener un ID mayor que `0`. `All` es el grupo `0` y no se puede usar.
- **La tarea falla porque no hay ningún motor seleccionado** — habilite al menos una de las opciones **Discover MySQL servers** o **Discover MariaDB servers**.
- **No se descubre ningún servidor** — compruebe la entidad de servicio en este orden: los valores de la credencial, después que tenga el rol **Reader** sobre el ámbito correcto, y después si **Resource group** o **Server name** están filtrando los servidores. Estos campos comparan valores completos y sin distinguir mayúsculas separados por `;`; no son expresiones regulares.
- **Un motor aparece como no disponible** — registre su proveedor de recursos en la suscripción (`Microsoft.DBforMySQL` o `Microsoft.DBforMariaDB`). El otro motor se sigue descubriendo.
- **Un agente sobrevive con `Azure Database Connection` a `0`** — el servidor está en la caché de entidades pero ya no es descubrible, porque se eliminó o se renombró. El agente se conserva hasta que la caché se reconstruye, lo que ocurre tras **Re-scan entities file interval**.
- **Un servidor detenido sigue teniendo `Azure Database Connection` a `1`** — la accesibilidad del recurso de Azure y el estado del servidor son cosas distintas: **`Database online`** informa de `0` para un servidor detenido.
- **Faltan algunos módulos de métricas** — puede que un servidor no exponga todas las métricas, o que no admita la agregación que usa el plugin. El plugin pregunta a Azure por las definiciones de métricas admitidas y omite las que no están disponibles. Por ejemplo, el almacenamiento de binlog solo está disponible en servidores MySQL con el registro binario habilitado.
- **Las peticiones fallan contra una nube soberana o personalizada** — configure **API endpoint** y **Login endpoint**. Los valores vacíos usan `https://management.azure.com` y `https://login.microsoftonline.com`.
- **Las peticiones agotan el tiempo** — suba **Request timeout**. El valor mínimo aplicado es `30` segundos.
- **Debug** muestra las excepciones completas durante una ejecución manual; déjelo desactivado en producción.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Azure credentials

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Azure credentials | `_credentials_` | select | — | Credencial de Azure del almacén de credenciales de Pandora FMS. Obligatorio |
| API endpoint | `_apiendpoint_` | string | — | Endpoint de Azure Resource Manager. Vacío usa `https://management.azure.com` |
| Login endpoint | `_loginendpoint_` | string | — | Endpoint de autenticación de Azure. Vacío usa `https://login.microsoftonline.com` |

#### Database discovery

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Resource group | `_resourcegroup_` | string | — | Filtro exacto de Resource Group, separado por `;`. Vacío descubre todos los Resource Groups |
| Server name | `_servername_` | string | — | Filtro exacto de servidor, separado por `;`. Vacío descubre todos los servidores |
| Discover MySQL servers | `_discovermysql_` | checkbox | on | Incluye servidores MySQL flexible y single |
| Discover MariaDB servers | `_discovermariadb_` | checkbox | on | Incluye servidores MariaDB |
| Create agent per server | `_agentperserver_` | checkbox | on | Deshabilitado envía todos los módulos a **Target agent** |
| Target agent | `_targetagent_` | string | `Azure Databases` | Agente usado en modo consolidado |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` cuando está habilitado, en el modo `1` en caso contrario |
| Agent prefix | `_agentprefix_` | string | — | Prefijo antepuesto a los nombres de los agentes por servidor |
| Module prefix | `_moduleprefix_` | string | — | Prefijo antepuesto a todos los nombres de módulo generados |
| Enable entities file re-scan interval | `_enableentitiesinterval_` | checkbox | off | Reutiliza la caché de servidores descubiertos hasta que el intervalo expira |
| Re-scan entities file interval | `_entitiesinterval_` | select | `86400` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Request timeout | `_timeout_` | number | `30` | Tiempo de espera HTTP de Azure en segundos. El valor mínimo aplicado es `30` |

#### Modules

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Performance modules | `_performance_` | checkbox | on | CPU, memoria y porcentaje de E/S de almacenamiento |
| Storage modules | `_storage_` | checkbox | on | Almacenamiento, log del servidor, copias y binlog |
| Connection modules | `_connections_` | checkbox | on | Conexiones activas, fallidas, totales y abortadas |
| Traffic modules | `_traffic_` | checkbox | on | Red de entrada y red de salida |
| Replication modules | `_replication_` | checkbox | on | Retraso de replicación y estado de los hilos de réplica |
| Engine modules | `_engine_` | checkbox | on | Consultas, consultas lentas, InnoDB y bloqueos |

### Claves del archivo de configuración

La tarea de Discovery construye este archivo a partir de sus propios campos; una ejecución manual lo suministra con `--conf`. Tiene una sección `[CONF]`.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `credentials` | Credencial de Azure codificada en base64 generada por Pandora FMS | Vacío |
| `tenant_id`, `subscription_id`, `client_id`, `client_secret` | Valores de credencial manuales, usados cuando no se proporciona `credentials` | Vacío |
| `api_endpoint` | Endpoint de Azure Resource Manager | `https://management.azure.com` |
| `login_endpoint` | Endpoint de autenticación de Azure | `https://login.microsoftonline.com` |
| `resource_group` | Filtro exacto de Resource Group, separado por `;` | Vacío |
| `server_name` | Filtro exacto de servidor, separado por `;` | Vacío |
| `discover_mysql` | Descubre servidores MySQL flexible y single | `1` |
| `discover_mariadb` | Descubre servidores MariaDB | `1` |
| `agent_per_server` | Crea un agente por servidor cuando está habilitado | `1` |
| `target_agent` | Agente usado en modo consolidado | `Azure Databases` |
| `agent_autodisable` | Usa el modo `2` de Pandora FMS cuando está habilitado y el modo `1` en caso contrario | `0` |
| `agent_prefix` | Prefijo de los nombres de los agentes por servidor | Vacío |
| `module_prefix` | Prefijo de todos los nombres de módulo generados | Vacío |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` |
| `group_id` | ID de grupo de Pandora FMS asignado a los agentes generados. Debe ser mayor que `0` | Obligatorio |
| `timeout` | Tiempo de espera HTTP en segundos. El valor mínimo aplicado es `30` | `30` |
| `entities_list` | Ruta del archivo de entidades | `/tmp/pandora_azure_database_entities.txt` |
| `enable_entities_interval` | Reconstruye el archivo de entidades tras el intervalo | `0` |
| `entities_interval` | Intervalo de reconstrucción del archivo de entidades en segundos | `86400` |
| `performance_metrics_enabled` | Habilita los módulos de rendimiento | `1` |
| `storage_metrics_enabled` | Habilita los módulos de almacenamiento | `1` |
| `connection_metrics_enabled` | Habilita los módulos de conexiones | `1` |
| `traffic_metrics_enabled` | Habilita los módulos de tráfico | `1` |
| `replication_metrics_enabled` | Habilita los módulos de replicación | `1` |
| `engine_metrics_enabled` | Habilita los módulos del motor | `1` |

El archivo de entidades se delimita por tarea: el plugin añade un hash de la suscripción, los endpoints, la selección de motores y los filtros, de modo que las cachés de tareas distintas nunca se mezclan.

### Ejecución por línea de comandos

El plugin lee un único archivo de configuración. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de tarea.

```bash
./pandora_azure_database --conf <PATH_TO_CONFIG>
```

Todas las claves de configuración también se pueden pasar como opción de línea de comandos, que tiene prioridad sobre el archivo:

| Opción | Descripción |
| --- | --- |
| `--conf`, `-c` | Ruta del archivo de configuración |
| `--credentials` | Credencial de Azure codificada en base64 |
| `--tenant-id` | Identificador del tenant de Azure |
| `--subscription-id` | Identificador de la suscripción de Azure |
| `--client-id` | Identificador de aplicación de la entidad de servicio |
| `--client-secret` | Secreto de la entidad de servicio |
| `--api-endpoint` | Endpoint de Azure Resource Manager |
| `--login-endpoint` | Endpoint de autenticación de Azure |
| `--resource-group` | Filtro exacto de Resource Group, separado por `;` |
| `--server-name` | Filtro exacto de servidor, separado por `;` |
| `--discover-mysql` | Habilita el descubrimiento de servidores MySQL |
| `--discover-mariadb` | Habilita el descubrimiento de servidores MariaDB |
| `--agent-per-server` | Habilita un agente por servidor |
| `--target-agent` | Agente de destino en modo consolidado |
| `--agent-autodisable` | Habilita el modo autodisable de agente |
| `--agent-prefix` | Prefijo opcional de agente |
| `--module-prefix` | Prefijo opcional de módulo |
| `--interval` | Intervalo del agente en segundos |
| `--group-id` | Identificador del grupo de agentes. Debe ser mayor que `0` |
| `--timeout` | Tiempo de espera HTTP en segundos. El valor mínimo aplicado es `30` |
| `--entities-list` | Ruta del archivo de entidades |
| `--enable-entities-interval` | Habilita la reconstrucción periódica del archivo de entidades |
| `--entities-interval` | Intervalo de reconstrucción del archivo de entidades |
| `--performance-metrics-enabled` | Habilita los módulos de rendimiento |
| `--storage-metrics-enabled` | Habilita los módulos de almacenamiento |
| `--connection-metrics-enabled` | Habilita los módulos de conexiones |
| `--traffic-metrics-enabled` | Habilita los módulos de tráfico |
| `--replication-metrics-enabled` | Habilita los módulos de replicación |
| `--engine-metrics-enabled` | Habilita los módulos del motor |
| `--debug` | Muestra las excepciones completas |

Un archivo de configuración mínimo para una ejecución manual:

```ini
[CONF]
subscription_id=<SUBSCRIPTION_ID>
tenant_id=<TENANT_ID>
client_id=<CLIENT_ID>
client_secret=<CLIENT_SECRET>
group_id=<GROUP_ID>
```

Ese archivo contiene una credencial en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin, manténgalo fuera de directorios compartidos y del control de versiones, y prefiera el almacén de credenciales de Pandora FMS para las ejecuciones de tarea, donde la tarea referencia la credencial en lugar de transportar el secreto.

### Módulos generados

Los módulos se llaman `[Module prefix]<nombre base>` en modo por servidor, y `[Module prefix]<servidor> <nombre base>` en modo consolidado. Todos los módulos de métricas son `generic_data` y solo se crean cuando el servidor expone la métrica y admite su agregación.

**Creados siempre**

- `Azure Database Connection`: `generic_proc`, `1` para un servidor descubierto y `0` para una entidad desaparecida.
- `Database online`: `generic_proc`, `1` cuando el estado del servidor es `Ready`, `Online` o `Running`, `0` en caso contrario.
- `Public network access`: `generic_proc`, `1` cuando Azure informa de acceso público a la red como `Enabled`, `0` cuando es `Disabled`. Solo se crea cuando Azure devuelve la propiedad.

**Módulos de rendimiento** (average)

| Módulo | Métrica de Azure | Unidad |
| --- | --- | --- |
| `CPU percent` | `cpu_percent` | `%` |
| `Memory percent` | `memory_percent` | `%` |
| `Storage IO percent` | `io_consumption_percent` | `%` |

**Módulos de almacenamiento**

| Módulo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- |
| `Storage used GB` | `storage_used` | average | `GB` |
| `Storage used percent` | `storage_percent` | average | `%` |
| `Storage limit GB` | `storage_limit` | maximum | `GB` |
| `Server log used GB` | `serverlog_storage_usage` | average | `GB` |
| `Server log used percent` | `serverlog_storage_percent` | average | `%` |
| `Backup storage used GB` | `backup_storage_used` | average | `GB` |
| `Binlog storage used GB` | `binlog_storage_used` | average | `GB` |

**Módulos de conexiones**

| Módulo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- |
| `Active connections` | `active_connections` | average | `Count` |
| `Failed connections` | `connections_failed` | total | `Count` |
| `Total connections` | `total_connections` | total | `Count` |
| `Aborted connections` | `aborted_connections` | total | `Count` |

**Módulos de tráfico** (total)

| Módulo | Métrica de Azure | Unidad |
| --- | --- | --- |
| `Network in MB` | `network_bytes_ingress` | `MB` |
| `Network out MB` | `network_bytes_egress` | `MB` |

**Módulos de replicación**

| Módulo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- |
| `Replication lag seconds` | `replication_lag` o `seconds_behind_master` | average | `s` |
| `Replica IO running` | `Replica_IO_Running` | maximum | `Count` |
| `Replica SQL running` | `Replica_SQL_Running` | maximum | `Count` |

**Módulos del motor** (total)

| Módulo | Métrica de Azure | Unidad |
| --- | --- | --- |
| `Queries` | `Queries` | `Count` |
| `Slow queries` | `Slow_queries` | `Count` |
| `Threads running` | `Threads_running` | `Count` |
| `InnoDB buffer pool reads` | `Innodb_buffer_pool_reads` | `Count` |
| `InnoDB buffer pool read requests` | `Innodb_buffer_pool_read_requests` | `Count` |
| `Deadlocks` | `lock_deadlocks` | `Count` |
| `Lock timeouts` | `lock_timeouts` | `Count` |

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| Nombre corto de la aplicación | `pandorafms.azure.database` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |
