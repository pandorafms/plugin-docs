# Azure SQL Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de Azure SQL descubre las bases de datos Azure SQL de una suscripción de Microsoft Azure y convierte su estado y sus métricas de Azure Monitor en agentes y módulos de Pandora FMS: rendimiento de CPU, DTU y E/S, uso de almacenamiento, conexiones, uso de TempDB y XTP, e interbloqueos.

Por defecto crea **un agente por base de datos**, llamado `[Agent prefix]Azure SQL <servidor>/<base de datos>`. También puede consolidar todas las bases de datos descubiertas en un único **Target agent**, con el servidor y la base de datos antepuestos a cada nombre de módulo. Cada agente lleva un módulo de disponibilidad, un módulo de base de datos en línea y un módulo por grupo de métricas habilitado.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.azure.sql`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Una suscripción de Azure con recursos Azure SQL Database | `Requerido` | El plugin descubre y lee bases de datos Azure SQL. Prerrequisito, no una declaración de compatibilidad |
| Una entidad de servicio de Microsoft Entra con permisos de lectura sobre la suscripción o el Resource Group | `Requerido` | El plugin lista servidores y bases de datos SQL y lee sus métricas de Azure Monitor. Normalmente el rol `Reader` es suficiente. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure) |
| Un grupo de agentes de Pandora FMS con ID mayor que `0` | `Requerido` | El grupo `All` tiene ID `0` y no se puede usar |
| Nubes de Azure soberanas o personalizadas | `Sin validar` | Los endpoints son configurables, pero ningún registro de pruebas establece su funcionamiento contra una nube no pública |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga bases de datos Azure SQL.
3. **Una credencial de Azure** guardada en el almacén de credenciales de Pandora FMS, o sus valores suministrados directamente para una ejecución manual.
4. **Un grupo de agentes válido** para la tarea. El grupo `All` no es válido, porque su ID es `0`.

El plugin se distribuye como un ejecutable autocontenido: la aplicación Discovery empaquetada incluye `bin/pandora_azure_sql`, por lo que no es necesario instalar ningún runtime adicional en el servidor de Pandora FMS ni para una ejecución manual.

### Preparar el acceso a Azure

Cree una entidad de servicio de Microsoft Entra con permisos de solo lectura y asígnele el rol **Reader** sobre la suscripción o el Resource Group que se vaya a descubrir. En la mayoría de entornos `Reader` es suficiente; cuando el acceso se limita a un único Resource Group, configure también el campo **Resource group** en la tarea. La entidad de servicio debe poder:

- Listar los recursos `Microsoft.Sql/servers`.
- Listar los recursos `Microsoft.Sql/servers/databases`.
- Leer propiedades básicas de la base de datos, como estado, edición, SKU y tamaño máximo.
- Consultar las métricas de Azure Monitor de cada base de datos.

Guarde el **Client ID**, el **Application secret**, el **Tenant or domain name** y el **Subscription id** de la entidad de servicio como una credencial de Azure en el almacén de credenciales de Pandora FMS, de modo que la tarea haga referencia a la credencial en lugar de transportar el secreto.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Azure SQL** aparece en la categoría **Cloud** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure SQL**. El primer paso genérico del asistente define la tarea; el paquete añade **Azure credentials**, **SQL discovery** y **Modules**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo, servidor e intervalo. El grupo debe tener un ID mayor que `0`; `All` no se puede usar. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure credentials.** La credencial y los endpoints de Azure:

- **Azure credentials** selecciona la credencial de Azure guardada. Es obligatoria.
- **API endpoint** y **Login endpoint** sobrescriben los endpoints de Azure Resource Manager y de autenticación de Azure para nubes soberanas o personalizadas. Los valores vacíos usan los endpoints públicos de Azure.

![Paso Azure credentials de la tarea de Discovery de Azure SQL.](../assets/images/discovery/azure-sql/azure-credentials.png)

**Paso 3 — SQL discovery.** Qué descubrir y cómo se distribuyen los agentes:

- **Resource group**, **SQL server name** y **Database name** filtran el descubrimiento. Cada uno acepta varios valores exactos y sin distinguir mayúsculas, separados por `;`. Vacío descubre todo.
- **Create agent per database** decide la distribución de agentes, y **Target agent** solo se usa cuando está deshabilitado.
- **Agent prefix** y **Module prefix** se anteponen a los nombres de agente y de módulo.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS.
- **Enable entities file re-scan interval** y **Re-scan entities file interval** controlan cuánto tiempo se reutiliza la caché de bases de datos descubiertas antes de reconstruirse.
- **Skip master database** excluye la base de datos `master`.

![Paso SQL discovery de la tarea de Discovery de Azure SQL.](../assets/images/discovery/azure-sql/sql-discovery.png)

**Paso 4 — Modules.** Qué familias de métricas se recogen:

- **Performance modules**: CPU, DTU, lectura física de datos, escritura de log, sesiones y workers en porcentaje.
- **Storage modules**: espacio de datos usado y asignado.
- **Connection modules**: conexiones correctas, fallidas y bloqueadas por el firewall.
- **Tempdb and XTP modules**: tamaño de datos y log de TempDB, porcentaje de log de TempDB usado y porcentaje de almacenamiento XTP.
- **Deadlock modules**: el recuento de interbloqueos.

![Paso Modules de la tarea de Discovery de Azure SQL.](../assets/images/discovery/azure-sql/modules.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de `resources_discovered`, `resources_vanished`, `modules` y `errors`. Espere un recurso descubierto por base de datos y `errors` en `0`.

2. **Los agentes.** Con **Create agent per database** habilitado, aparece un agente por base de datos descubierta, llamado `[Agent prefix]Azure SQL <servidor>/<base de datos>`. Cada uno informa de `Azure` como sistema operativo y hereda el grupo y el intervalo de la tarea.

3. **`Azure SQL Connection`** es `1` en toda base de datos descubierta, y **`Database online`** es `1` cuando el estado de la base de datos es `Online` o `Ready`.

4. **Los módulos de métricas** de cada familia habilitada.

Si no aparece ningún agente, lo primero que hay que revisar son la credencial, sus permisos o los filtros.

![Resumen de ejecución de la tarea de Discovery de Azure SQL.](../assets/images/discovery/azure-sql/task-summary.png)

## Interpretar los resultados

### Distribución de agentes

**Con Create agent per database habilitado**, que es el valor por defecto, el plugin crea un agente por base de datos, llamado `[Agent prefix]Azure SQL <servidor>/<base de datos>`, con el FQDN del servidor como dirección y el ID del recurso de la base de datos como descripción.

**Con él deshabilitado**, todos los módulos van al único **Target agent** y el servidor y la base de datos se anteponen a cada nombre de módulo como `<servidor>/<base de datos> <nombre del módulo>`. Esto importa al leer los módulos: en modo consolidado el nombre del módulo identifica la base de datos.

Los agentes generados informan de `Azure` como sistema operativo, heredan el grupo y el intervalo de la tarea, y se crean en el modo `2` de Pandora FMS cuando **Agent autodisable mode** está habilitado, o en el modo `1` cuando está deshabilitado.

### Descubrimiento y filtros

Los filtros **Resource group**, **SQL server name** y **Database name** usan coincidencias exactas y sin distinguir mayúsculas, no expresiones regulares; separe varios valores con `;`. La opción **Skip master database** excluye la base de datos `master`.

Las bases de datos descubiertas se conservan en el archivo de entidades. Una entidad guardada que ya no aparece en un escaneo se cuenta en `resources_vanished` y genera solo `Azure SQL Connection` con valor `0`, de modo que una base de datos eliminada o renombrada queda visible en lugar de desaparecer en silencio. Cuando el intervalo de reescaneo expira, la caché se reconstruye sin comparar con las entidades anteriores.

### Qué se crea

| Habilitado por | Qué se obtiene |
| --- | --- |
| Siempre | `Azure SQL Connection` y `Database online` |
| Performance modules | `CPU percent`, `DTU consumption percent`, `Physical data read percent`, `Log write percent`, `Sessions percent`, `Workers percent` |
| Storage modules | `Data space used GB`, `Data space used percent`, `Data space allocated GB` |
| Connection modules | `Successful connections`, `Failed connections`, `Blocked by firewall connections` |
| Tempdb and XTP modules | `Tempdb data size MB`, `Tempdb log size MB`, `Tempdb log used percent`, `XTP storage percent` |
| Deadlock modules | `Deadlocks` |

El plugin lee las métricas de Azure Monitor y solo crea un módulo de métrica cuando la base de datos expone esa métrica y admite su agregación. El inventario exhaustivo de módulos, tipos, unidades y agregaciones está en [Módulos generados](#modulos-generados).

## Solución de problemas

- **La tarea falla por el grupo** — el grupo de agentes debe tener un ID mayor que `0`. `All` es el grupo `0` y no se puede usar.
- **No se descubre ninguna base de datos** — compruebe la entidad de servicio en este orden: los valores de la credencial, después que tenga el rol **Reader** sobre el ámbito correcto, y después si **Resource group**, **SQL server name** o **Database name** están filtrando las bases de datos. Estos campos comparan valores completos y sin distinguir mayúsculas separados por `;`; no son expresiones regulares.
- **Un agente sobrevive con `Azure SQL Connection` a `0`** — la base de datos está en la caché de entidades pero ya no es descubrible, porque se eliminó o se renombró. El agente se conserva hasta que la caché se reconstruye, lo que ocurre tras **Re-scan entities file interval**.
- **Faltan algunos módulos de métricas** — puede que una base de datos no exponga todas las métricas, o que no admita la agregación que usa el plugin. El plugin pregunta a Azure por las definiciones de métricas admitidas y omite las que no están disponibles.
- **Las peticiones fallan contra una nube soberana o personalizada** — configure **API endpoint** y **Login endpoint**. Los valores vacíos usan `https://management.azure.com` y `https://login.microsoftonline.com`.
- **Las peticiones agotan el tiempo** — suba el tiempo de espera de las peticiones en el archivo de configuración. El valor mínimo aplicado es `30` segundos.
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

#### SQL discovery

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Resource group | `_resourcegroup_` | string | — | Filtro exacto de Resource Group, separado por `;`. Vacío descubre todos los Resource Groups |
| SQL server name | `_servername_` | string | — | Filtro exacto de servidor SQL, separado por `;`. Vacío descubre todos los servidores |
| Database name | `_databasename_` | string | — | Filtro exacto de base de datos, separado por `;`. Vacío descubre todas las bases de datos |
| Create agent per database | `_agentperdatabase_` | checkbox | on | Deshabilitado envía todos los módulos a **Target agent** |
| Target agent | `_targetagent_` | string | `Azure SQL` | Agente usado en modo consolidado |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` cuando está habilitado, en el modo `1` en caso contrario |
| Agent prefix | `_agentprefix_` | string | — | Prefijo antepuesto a los nombres de los agentes por base de datos |
| Module prefix | `_moduleprefix_` | string | — | Prefijo antepuesto a todos los nombres de módulo generados |
| Enable entities file re-scan interval | `_enableentitiesinterval_` | checkbox | off | Reutiliza la caché de bases de datos descubiertas hasta que el intervalo expira |
| Re-scan entities file interval | `_entitiesinterval_` | select | `86400` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Skip master database | `_skipmaster_` | checkbox | on | Excluye la base de datos `master` |

#### Modules

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Performance modules | `_performance_` | checkbox | on | CPU, DTU, E/S, log, sesiones y workers en porcentaje |
| Storage modules | `_storage_` | checkbox | on | Espacio de datos usado y asignado |
| Connection modules | `_connections_` | checkbox | on | Conexiones correctas, fallidas y bloqueadas por el firewall |
| Tempdb and XTP modules | `_tempdbxtp_` | checkbox | on | Tamaño de datos y log de TempDB, porcentaje de log de TempDB usado y almacenamiento XTP |
| Deadlock modules | `_deadlocks_` | checkbox | on | Recuento de interbloqueos |

### Claves del archivo de configuración

La tarea de Discovery construye este archivo a partir de sus propios campos; una ejecución manual lo suministra con `--conf`. Tiene una sección `[CONF]`.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `credentials` | Credencial de Azure codificada en base64 generada por Pandora FMS | Vacío |
| `tenant_id`, `subscription_id`, `client_id`, `client_secret` | Valores de credencial manuales, usados cuando no se proporciona `credentials` | Vacío |
| `api_endpoint` | Endpoint de Azure Resource Manager | `https://management.azure.com` |
| `login_endpoint` | Endpoint de autenticación de Azure | `https://login.microsoftonline.com` |
| `resource_group` | Filtro exacto de Resource Group, separado por `;` | Vacío |
| `server_name` | Filtro exacto de servidor SQL, separado por `;` | Vacío |
| `database_name` | Filtro exacto de base de datos, separado por `;` | Vacío |
| `agent_per_database` | Crea un agente por base de datos cuando está habilitado | `1` |
| `target_agent` | Agente usado en modo consolidado | `Azure SQL` |
| `agent_autodisable` | Usa el modo `2` de Pandora FMS cuando está habilitado y el modo `1` en caso contrario | `0` |
| `agent_prefix` | Prefijo de los nombres de los agentes por base de datos | Vacío |
| `module_prefix` | Prefijo de todos los nombres de módulo generados | Vacío |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` |
| `group_id` | ID de grupo de Pandora FMS asignado a los agentes generados. Debe ser mayor que `0` | Obligatorio |
| `timeout` | Tiempo de espera HTTP en segundos. El valor mínimo aplicado es `30` | `30` |
| `scan_databases` | Habilita el descubrimiento de bases de datos | `1` |
| `entities_list` | Ruta del archivo de entidades | `/tmp/pandora_azure_sql_entities.txt` |
| `enable_entities_interval` | Reconstruye el archivo de entidades tras el intervalo | `0` |
| `entities_interval` | Intervalo de reconstrucción del archivo de entidades en segundos | `86400` |
| `skip_master_database` | Excluye la base de datos `master` | `1` |
| `performance_metrics_enabled` | Habilita los módulos de rendimiento | `1` |
| `storage_metrics_enabled` | Habilita los módulos de almacenamiento | `1` |
| `connection_metrics_enabled` | Habilita los módulos de conexiones | `1` |
| `tempdb_xtp_metrics_enabled` | Habilita los módulos de TempDB y XTP | `1` |
| `deadlock_metrics_enabled` | Habilita el módulo de interbloqueos | `1` |

El archivo de entidades está acotado por tarea: el plugin añade un hash de la suscripción, los endpoints y los filtros, por lo que las cachés de tareas distintas nunca se mezclan.

### Ejecución en línea de comandos

El plugin lee un único archivo de configuración. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de tarea.

```bash
./pandora_azure_sql --conf <PATH_TO_CONFIG>
```

Cada clave de configuración también se puede pasar como opción de línea de comandos, que sobrescribe el archivo:

| Opción | Descripción |
| --- | --- |
| `--conf`, `-c` | Ruta al archivo de configuración |
| `--credentials` | Credencial de Azure codificada en base64 |
| `--tenant-id` | Identificador de tenant de Azure |
| `--subscription-id` | Identificador de suscripción de Azure |
| `--client-id` | Identificador de aplicación de la entidad de servicio |
| `--client-secret` | Secreto de la entidad de servicio |
| `--api-endpoint` | Endpoint de Azure Resource Manager |
| `--login-endpoint` | Endpoint de autenticación de Azure |
| `--resource-group` | Filtro exacto de Resource Group, separado por `;` |
| `--server-name` | Filtro exacto de servidor SQL, separado por `;` |
| `--database-name` | Filtro exacto de base de datos, separado por `;` |
| `--agent-per-database` | Habilita un agente por base de datos |
| `--target-agent` | Agente de destino en modo consolidado |
| `--agent-autodisable` | Habilita el modo de autodesactivación de agentes |
| `--agent-prefix` | Prefijo de agente opcional |
| `--module-prefix` | Prefijo de módulo opcional |
| `--interval` | Intervalo del agente en segundos |
| `--group-id` | Identificador de grupo de agentes. Debe ser mayor que `0` |
| `--timeout` | Tiempo de espera HTTP en segundos. El valor mínimo aplicado es `30` |
| `--scan-databases` | Habilita el descubrimiento de bases de datos |
| `--entities-list` | Ruta del archivo de entidades |
| `--enable-entities-interval` | Habilita la reconstrucción periódica del archivo de entidades |
| `--entities-interval` | Intervalo de reconstrucción del archivo de entidades |
| `--skip-master-database` | Excluye la base de datos `master` |
| `--performance-metrics-enabled` | Habilita los módulos de rendimiento |
| `--storage-metrics-enabled` | Habilita los módulos de almacenamiento |
| `--connection-metrics-enabled` | Habilita los módulos de conexiones |
| `--tempdb-xtp-metrics-enabled` | Habilita los módulos de TempDB y XTP |
| `--deadlock-metrics-enabled` | Habilita el módulo de interbloqueos |
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

Ese archivo contiene una credencial en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin, manténgalo fuera de directorios compartidos y del control de versiones, y prefiera el almacén de credenciales de Pandora FMS para las ejecuciones de tarea, donde la tarea hace referencia a la credencial en lugar de transportarla.

### Módulos generados

Los módulos se llaman `[Module prefix]<nombre base>` en modo por base de datos, y `[Module prefix]<servidor>/<base de datos> <nombre base>` en modo consolidado. Todo módulo de métrica es `generic_data` y solo se crea cuando la base de datos expone la métrica y admite su agregación.

**Siempre se crean**

- `Azure SQL Connection`: `generic_proc`, `1` para una base de datos descubierta y `0` para una entidad desaparecida.
- `Database online`: `generic_proc`, `1` cuando el estado de la base de datos es `Online` o `Ready`, `0` en caso contrario.

**Módulos de rendimiento** (average)

- `CPU percent`: `%`.
- `DTU consumption percent`: `%`.
- `Physical data read percent`: `%`.
- `Log write percent`: `%`.
- `Sessions percent`: `%`.
- `Workers percent`: `%`.

**Módulos de almacenamiento** (average)

- `Data space used GB`: `GB`.
- `Data space used percent`: `%`.
- `Data space allocated GB`: `GB`.

**Módulos de conexiones** (total)

- `Successful connections`: `Count`.
- `Failed connections`: `Count`.
- `Blocked by firewall connections`: `Count`.

**Módulos de Tempdb y XTP** (average)

- `Tempdb data size MB`: `MB`.
- `Tempdb log size MB`: `MB`.
- `Tempdb log used percent`: `%`.
- `XTP storage percent`: `%`.

**Módulos de interbloqueos** (total)

- `Deadlocks`: `Count`.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.azure.sql` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |