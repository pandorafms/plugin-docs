# Discovery de VMware Horizon

*Última actualización del artículo: 2026-09-29.*

## Qué monitoriza

El plugin de Discovery de VMware Horizon se conecta a un entorno VMware Horizon a través de su API REST y convierte sus datos de inventario y monitorización en agentes y módulos de Pandora FMS: sesiones y usuarios, desktop pools, servidores RDS, máquinas, máquinas físicas, discos persistentes, métricas de salud, servidores de conexión, gateways, App Volumes, la base de datos de eventos, centros de datos virtuales, uso de licencias y métricas del sistema.

A diferencia de los plugins que crean un agente por cada recurso descubierto, este plugin consolida cada categoría de recurso habilitada en un **único agente**, con el nombre derivado del dominio y la URL configurados en la tarea. El nombre de cada módulo se prefija con su categoría de recurso para mantener los nombres únicos dentro del agente, y cada módulo lleva un marcador de recurso que permite al panel de consola complementario agrupar y filtrar los datos.

El plugin se ejecuta como una tarea de Discovery: la consola crea la tarea, el servidor de Discovery ejecuta el plugin y el agente y los módulos generados se crean automáticamente. La tarea entrega los datos generados a través de Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.2` (`pandorafms.horizon`) | Objetivo documentado | La versión que describe esta página, identificada por la definición del paquete |
| Un entorno VMware Horizon cuya API REST sea accesible | `Requerido` | El plugin se autentica y lee los endpoints de inventario y monitorización a través de la API REST de Horizon |
| Una cuenta de Horizon con acceso de lectura a los endpoints de inventario y monitorización | `Requerido` | El plugin se autentica y lee datos. Nunca modifica la configuración de Horizon |
| Una versión concreta de VMware Horizon | `Sin validar` | Ningún registro de pruebas publicado establece compatibilidad con una versión concreta de Horizon |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas publicado establece compatibilidad con sistemas operativos |

### Requisitos

- Un servidor Pandora FMS con Discovery habilitado para ejecutar la tarea y una consola para definirla.
- Un entorno VMware Horizon cuya API REST sea accesible desde el servidor que ejecuta el plugin. El plugin lo aborda a través de la URL configurada en la tarea.
- Una cuenta de Horizon capaz de autenticarse con el dominio configurado y leer los endpoints de inventario y monitorización que use la tarea. Concede únicamente los permisos de lectura que requiera tu monitorización.
- Un grupo de agentes de destino y un intervalo de monitorización para el agente generado. Ambos proceden de la tarea de Discovery y los hereda el agente generado.
- Accesibilidad de red al destino de Tentacle, porque la tarea transfiere los datos generados a través de Tentacle.
- El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que el servidor de Discovery ejecuta.

### Preparar el acceso a Horizon

El plugin se autentica en la API REST de Horizon con el **Domain**, el **Username** y el **Password** configurados en la tarea, y usa el token de acceso devuelto para las peticiones de inventario y monitorización. Solo lee datos de Horizon y nunca modifica su configuración, por lo que basta con una cuenta de solo lectura.

La conexión no verifica el certificado TLS que presenta el endpoint de Horizon, así que ejecuta la tarea únicamente sobre una red de confianza o a través de un túnel protegido.

### Instalar el plugin

Carga el paquete `.disco` desde **Management → Discovery → Manage disco packages**: elige **Select a file**, selecciona el paquete y haz clic en **Upload DISCO**. Una vez cargado, **VMware Horizon** aparece en la lista de paquetes y en la sección **Applications** del asistente de Discovery.

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Applications → VMware Horizon**. El asistente recorre la definición genérica de la tarea y dos pasos del plugin: **Horizon base** y **Agent selection**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Definición de la tarea

El paso genérico solicita el **nombre** de la tarea, el **grupo de agentes** y el **servidor** en el que se ejecuta, y el **intervalo**. El grupo y el intervalo se pasan al plugin y los hereda el agente generado.

### Paso 2 — Horizon base

Detalles de conexión y destino de Tentacle:

- **Domain** es el dominio de Horizon que se usa para autenticarse.
- **Url** es la URL base del entorno Horizon al que conectarse, por ejemplo `https://horizon.example.com`.
- **Username** y **Password** son las credenciales de Horizon.
- **Use prefix** muestra el campo **Prefix**, que la versión actual del plugin no aplica al nombre del agente ni al de los módulos.
- **Max threads** está presente en el asistente, pero la versión actual del plugin no lo usa.
- **Tentacle IP**, **Tentacle port** y **Tentacle extra options** definen cómo se envían los datos generados. Deja los valores por defecto salvo que tu entorno necesite otro destino de Tentacle.

![Paso Horizon base del asistente con los campos Domain, Url, Username, Password, Use prefix, Max threads, Tentacle IP y Tentacle port.](../assets/images/discovery/vmware-horizon/horizon-base.png)

### Paso 3 — Agent selection

Qué categorías de recurso recoge la tarea. Todas están habilitadas por defecto:

- **Desktop Pools**, **RDS Servers**, **Sessions**, **Machines**, **Physical Machines**, **Persistent Disks**, **Health Metrics**, **Connection Servers**, **App Volumes**, **Event Database**, **Gateways**, **Usage Metrics**, **System Metrics** y **Virtual Datacenters**.

Desactivar una categoría elimina sus módulos del agente generado; el plugin no consulta los endpoints de una categoría deshabilitada.

![Paso Agent selection del asistente con los catorce interruptores de categoría de recurso.](../assets/images/discovery/vmware-horizon/agent-selection.png)

## Verificar la primera ejecución

Fuerza la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea** informa de `Total agents` y `Total modules`. Se espera `Total agents` en `1`, porque el plugin consolida todas las categorías habilitadas en un único agente.

2. **El agente generado.** Se nombra `<domain> - <url>`, de modo que una tarea con dominio `mock.local` y URL `https://horizon-mock:8000` produce el agente `mock.local - horizon-mock:8000`. Hereda el grupo y el intervalo de la tarea.

3. **Los módulos.** El agente lleva un módulo por cada métrica recogida, prefijado con su categoría de recurso, por ejemplo `Sessions - Total Sessions` o `Gateways - gw-01 Status`.

![Resumen de ejecución de la tarea con Total agents 1 y Total modules 138.](../assets/images/discovery/vmware-horizon/task-summary.png)

![Lista de gestión de agentes con el único agente VMware Horizon generado.](../assets/images/discovery/vmware-horizon/managed-agent.png)

![Módulos del agente generado, prefijados con la categoría de recurso.](../assets/images/discovery/vmware-horizon/agent-modules.png)

Si no aparece ningún agente, lo primero que hay que revisar es la URL, el dominio y las credenciales.

## Entender los resultados

### Diseño y nombre del agente

El plugin crea **un agente por tarea**, no un agente por recurso. El nombre del agente se construye a partir del dominio y la URL de la tarea como `<domain> - <url>`, eliminando el esquema de la URL y sustituyendo cualquier carácter que no sea letra, dígito, punto, guion bajo, guion o dos puntos por un guion. Por tanto, dos tareas configuradas con el mismo dominio y la misma URL abordan el mismo agente.

Como todas las categorías comparten un agente, los nombres de módulo se prefijan con la categoría de recurso (`<Category> - <métrica>`) para mantenerlos únicos. Esto importa al leer los resultados: un módulo como `Connection Servers - CS-01 Status` pertenece a la categoría Connection Servers, y un mismo nombre de campo puede aparecer bajo otra categoría con un prefijo distinto.

Los recursos eliminados de Horizon no se borran automáticamente de Pandora FMS.

### Grupos de módulos

| Categoría | Qué recoge |
| --- | --- |
| Desktop Pools | Máquinas, sesiones conectadas y ocupación por desktop pool |
| RDS Servers | Estado y status del servidor, indicador de habilitado, número de sesiones, índice de carga y máximo de sesiones configurado |
| Sessions | Sesiones y usuarios totales, estados de sesión de escritorio, aplicación y RDS, plataformas cliente, protocolos y recuentos de gateways |
| Machines | Estado de la máquina, estado de emparejamiento, memoria, capacidad de disco y última hora de mantenimiento |
| Physical Machines | Disponibilidad de cada máquina física |
| Persistent Disks | Capacidad, uso, estado, máquina, datastore y última conexión por disco |
| Health Metrics | Recuentos healthy, warning, error, unknown y total por componente |
| Connection Servers | Estado, conexiones, conexiones de túnel, umbral de sesiones y replicaciones por servidor |
| App Volumes | Estado, validez de certificado y aceptación de huella por servidor de conexión |
| Event Database | Recuento de eventos y estado de la base de datos de eventos de Horizon |
| Gateways | Estado y recuentos de conexiones activas, BLAST y PCOIP por gateway |
| Usage Metrics | Uso de licencias actual y máximo de sesiones, conexiones y usuarios con nombre |
| System Metrics | Errores y avisos de eventos, hosts RDS y máquinas virtuales de vCenter con problemas, y recuento de sesiones |
| Virtual Datacenters | Hosts, datastores y servidores de conexión, con capacidad, uso y estado |

El inventario exhaustivo de módulos está en [Módulos generados](#modulos-generados).

### Dashboard de consola complementario

Una extensión de consola complementaria, **VMware Horizon Dashboard**, presenta los datos recogidos como un panel en **Monitoring**. Lee los marcadores de recurso que escribe el plugin y ofrece dos filtros, **Agent** y **Resource**, además de un periodo de gráfica, de modo que puede revisarse por separado un entorno Horizon o una categoría de recurso.

![Panel VMware Horizon Dashboard con los paneles de sesiones, licencias y sistema y las cuatro gráficas de distribución.](../assets/images/discovery/vmware-horizon/dashboard-overview.png)

![Paneles de infraestructura del panel VMware Horizon Dashboard: evolución de sesiones, servidores de conexión, gateways, desktop pools, métricas de salud y servidores RDS.](../assets/images/discovery/vmware-horizon/dashboard-infrastructure.png)

![Paneles de centro de datos virtual del panel VMware Horizon Dashboard: hosts, datastores, máquinas, discos persistentes, App Volumes, base de datos de eventos y máquinas físicas.](../assets/images/discovery/vmware-horizon/dashboard-datacenters.png)

## Resolución de problemas

- **La tarea informa de un error de autenticación** — revisa **Url**, **Domain**, **Username** y **Password**, y confirma que el endpoint de Horizon es accesible y acepta la cuenta.
- **No se genera ningún agente** — confirma que la URL es accesible desde el servidor que ejecuta el plugin y que hay al menos una categoría de recurso habilitada.
- **Falta un grupo de módulos** — la categoría correspondiente está deshabilitada en el paso **Agent selection**. Las categorías deshabilitadas no se consultan y sus módulos no se generan.
- **La tarea termina bien pero algunos endpoints informan de errores** — la ejecución continúa cuando falla un endpoint concreto; la información de ejecución de la tarea detalla el endpoint que ha fallado y su estado HTTP.
- **Las peticiones fallan con un estado HTTP reintentable** — el plugin reintenta los estados HTTP `429`, `500`, `502`, `503` y `504` hasta tres veces antes de registrar un error.
- **Falla la transferencia por Tentacle** — confirma que el servidor que ejecuta el plugin puede alcanzar **Tentacle IP** en **Tentacle port**.
- **Los recursos eliminados de Horizon permanecen en Pandora FMS** — los agentes y módulos generados no se borran automáticamente. Elimínalos manualmente si ya no son necesarios.

## Operar

### Ejecución manual

El plugin también puede ejecutarse fuera del asistente de Discovery con un fichero de configuración. Resulta útil para probar la conectividad o para una ejecución puntual. El fichero lo construye la tarea de Discovery para una ejecución normal; una ejecución manual suministra las mismas claves.

```bash
./pandora_horizon --conf <PATH_TO_CONFIG>
```

Un fichero de configuración mínimo:

```ini
[CONF]
domain=<DOMAIN>
url=<HORIZON_URL>
user=<USERNAME>
password=<PASSWORD>
agents_group_name=<GROUP_NAME>
interval=300
tentacle_ip=127.0.0.1
tentacle_port=41121
```

Ese fichero contiene una credencial en texto plano. Restríngelo a la cuenta que ejecuta el plugin y mantenlo fuera de directorios compartidos y del control de versiones.

## Referencia

### Parámetros de la tarea

La consola presenta estos campos después de la definición genérica de la tarea. La columna macro es el identificador que se usa en la configuración generada de la tarea.

#### Horizon base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Domain | `_domain_` | string | — | Dominio de Horizon que se usa para autenticarse |
| Url | `_url_` | string | — | URL base del entorno Horizon. Obligatorio |
| Username | `_username_` | string | — | Usuario de Horizon. Obligatorio |
| Password | `_password_` | password | — | Contraseña de Horizon. Obligatoria |
| Use prefix | `_usePrefix_` | checkbox | off | Muestra el campo **Prefix**. La versión actual del plugin no lo aplica |
| Prefix | `_prefix_` | string | — | Solo se muestra cuando **Use prefix** está habilitado. La versión actual del plugin no lo aplica |
| Max threads | `_threads_` | number | `1` | Presente en el asistente. La versión actual del plugin no lo usa |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Destino de la transferencia por Tentacle |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de destino de la transferencia por Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | string | — | Opciones extra que se pasan al cliente de Tentacle |

#### Agent selection

Cada campo siguiente es una casilla, habilitada por defecto, que activa una categoría de recurso.

| Campo | Macro |
| --- | --- |
| Desktop Pools | `_monitorDesktopPools_` |
| RDS Servers | `_monitorRdsServers_` |
| Sessions | `_monitorSessions_` |
| Machines | `_monitorMachines_` |
| Physical Machines | `_monitorPhysicalMachines_` |
| Persistent Disks | `_monitorPersistentDisks_` |
| Health Metrics | `_monitorHealthMetrics_` |
| Connection Servers | `_monitorConnectionServers_` |
| App Volumes | `_monitorAppVolumes_` |
| Event Database | `_monitorEventDatabase_` |
| Gateways | `_monitorGateways_` |
| Usage Metrics | `_monitorUsageMetrics_` |
| System Metrics | `_monitorSystemMetrics_` |
| Virtual Datacenters | `_monitorVirtualDatacenters_` |

### Claves del fichero de configuración

La tarea de Discovery construye este fichero a partir de sus propios campos; una ejecución manual lo suministra con `--conf`.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `agents_group_name` | Grupo de agentes asignado al agente generado | Heredado de la tarea |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` en ejecuciones manuales |
| `domain` | Dominio de Horizon que se usa para autenticarse | Vacío |
| `url` | URL base del entorno Horizon | Vacío |
| `user` | Usuario de Horizon | Vacío |
| `password` | Contraseña de Horizon | Vacío |
| `transfer_mode` | Modo de entrega; `tentacle` envía los datos a través de Tentacle | `tentacle` |
| `tentacle_ip` | Dirección de destino de Tentacle | `127.0.0.1` |
| `tentacle_port` | Puerto de destino de Tentacle | `41121` |
| `tentacle_client` | Comando del cliente de Tentacle | `tentacle_client` |
| `tentacle_opts` | Opciones extra que se pasan al cliente de Tentacle | Vacío |
| `data_dir` | Directorio de entrada de datos | `/var/spool/pandora/data_in/` |
| `temporal` | Carpeta de trabajo para ficheros temporales | `/tmp` |
| `monitor_desktop_pools` | Recoge la categoría Desktop Pools | `1` |
| `monitor_rds_servers` | Recoge la categoría RDS Servers | `1` |
| `monitor_sessions` | Recoge la categoría Sessions | `1` |
| `monitor_machines` | Recoge la categoría Machines | `1` |
| `monitor_physical_machines` | Recoge la categoría Physical Machines | `1` |
| `monitor_persistent_disks` | Recoge la categoría Persistent Disks | `1` |
| `monitor_health_metrics` | Recoge la categoría Health Metrics | `1` |
| `monitor_connection_servers` | Recoge la categoría Connection Servers | `1` |
| `monitor_app_volumes` | Recoge la categoría App Volumes | `1` |
| `monitor_event_database` | Recoge la categoría Event Database | `1` |
| `monitor_gateways` | Recoge la categoría Gateways | `1` |
| `monitor_usage_metrics` | Recoge la categoría Usage Metrics | `1` |
| `monitor_system_metrics` | Recoge la categoría System Metrics | `1` |
| `monitor_virtual_datacenters` | Recoge la categoría Virtual Datacenters | `1` |

### Módulos generados

El nombre de cada módulo se prefija con su categoría de recurso, `<Category> - <métrica>`. Las tablas siguientes listan la parte de métrica; la categoría es la del encabezado de cada grupo. El tipo `generic_data` es numérico y `generic_data_string` es texto.

#### Desktop Pools

Un conjunto por desktop pool. `<pool>` es el nombre visible del desktop pool.

| Módulo | Tipo |
| --- | --- |
| `<pool> num_machines` | generic_data |
| `<pool> num_connected_sessions` | generic_data |
| `<pool> occupancy_count` | generic_data |

#### RDS Servers

Un conjunto por servidor RDS. `<server>` es el nombre del servidor.

| Módulo | Tipo |
| --- | --- |
| `<server> Agent Build` | generic_data_string |
| `<server> Agent Version` | generic_data_string |
| `<server> Max Sessions Count Configured` | generic_data |
| `<server> Operating System` | generic_data_string |
| `<server> State` | generic_data_string |
| `<server> Enabled` | generic_data |
| `<server> Farm ID` | generic_data_string |
| `<server> Server ID` | generic_data_string |
| `<server> Load Index` | generic_data |
| `<server> Load Preference` | generic_data_string |
| `<server> Name` | generic_data_string |
| `<server> Session Count` | generic_data |
| `<server> Status` | generic_data_string |

El endpoint de inventario también produce un módulo por cada campo devuelto, nombrado `<nombre del servidor><nombre del campo>`.

#### Sessions

| Módulo | Tipo |
| --- | --- |
| `Sessions` | generic_data |
| `Total Sessions` | generic_data |
| `Total Users` | generic_data |
| `Active App Sessions`, `Disconnected App Sessions`, `Idle App Sessions`, `Pending App Sessions` | generic_data |
| `Active Desktop Sessions`, `Disconnected Desktop Sessions`, `Idle Desktop Sessions`, `Pending Desktop Sessions` | generic_data |
| `Active RDS Sessions`, `Disconnected RDS Sessions`, `Idle RDS Sessions`, `Pending RDS Sessions` | generic_data |
| `Android Clients`, `Browser Clients`, `iOS Clients`, `Linux Clients`, `Mac Clients`, `Other Clients`, `Windows Clients` | generic_data |
| `BLAST Sessions`, `PCOIP Sessions`, `RDP Sessions`, `Other Protocols` | generic_data |
| `External Gateways`, `Internal Gateways`, `Unknown Gateways` | generic_data |

#### Machines

Un conjunto por máquina gestionada. `<machine>` es el nombre de host cuando los datos de la máquina gestionada lo proporcionan, o el nombre de la máquina en caso contrario.

| Módulo | Tipo | Notas |
| --- | --- | --- |
| `<machine> State` | generic_data_string | |
| `<machine> Pairing State` | generic_data_string | |
| `<machine> Memory MB` | generic_data | Cuando se informa |
| `<machine> Operation State` | generic_data_string | Cuando se informa |
| `<machine> Last Maintenance Time` | generic_data | Cuando se informa, unidad `_timeticks_` |
| `<machine> Disk Capacity MB` | generic_data | Uno por cada disco virtual informado |

#### Physical Machines

Un módulo por máquina física, de tipo `generic_proc`, con valor `1` cuando el estado de la máquina es `AVAILABLE` y `0` en caso contrario. Su descripción registra el estado y el sistema operativo.

#### Persistent Disks

Un conjunto por disco persistente. `<disk>` es el nombre del disco.

| Módulo | Tipo |
| --- | --- |
| `<disk> Access Group ID` | generic_data_string |
| `<disk> Capacity MB` | generic_data |
| `<disk> Datastore ID` | generic_data_string |
| `<disk> Datastore Name` | generic_data_string |
| `<disk> Desktop Pool ID` | generic_data_string |
| `<disk> Desktop Pool Name` | generic_data_string |
| `<disk> Disk ID` | generic_data_string |
| `<disk> Last Attached Time` | generic_data |
| `<disk> Machine ID` | generic_data_string |
| `<disk> Machine Name` | generic_data_string |
| `<disk> Status` | generic_data_string |
| `<disk> Usage` | generic_data |
| `<disk> User ID` | generic_data_string |
| `<disk> User Name` | generic_data_string |
| `<disk> vCenter ID` | generic_data_string |

#### Health Metrics

Un conjunto por componente. `<component>` es el nombre del componente.

| Módulo | Tipo |
| --- | --- |
| `<component> Error Count` | generic_data |
| `<component> Healthy Count` | generic_data |
| `<component> Total Count` | generic_data |
| `<component> Unknown Count` | generic_data |
| `<component> Warning Count` | generic_data |

#### Connection Servers

Un conjunto por servidor de conexión. `<server>` es el nombre del servidor.

| Módulo | Tipo |
| --- | --- |
| `<server> Connection Count` | generic_data |
| `<server> CS Replications` | generic_data |
| `<server> Last Updated Timestamp` | generic_data |
| `<server> Name` | generic_data_string |
| `<server> Services` | generic_data_string |
| `<server> Session Protocol Data` | generic_data_string |
| `<server> Session Threshold` | generic_data |
| `<server> Status` | generic_data_string |
| `<server> Tunnel Connection Count` | generic_data |
| `<server> Unrecognized PCOIP Requests Count` | generic_data |
| `<server> Unrecognized Tunnel Requests Count` | generic_data |
| `<server> Unrecognized XMLAPI Requests Count` | generic_data |

#### App Volumes

Un conjunto por servidor de conexión informado por un gestor de App Volumes. `<server>` es el nombre del servidor de conexión.

| Módulo | Tipo |
| --- | --- |
| `<server> Certificate Valid` | generic_data |
| `<server> Certificate Valid From` | generic_data_string |
| `<server> Certificate Valid To` | generic_data_string |
| `<server> Status` | generic_data_string |
| `<server> Thumbprint Accepted` | generic_data |

#### Event Database

| Módulo | Tipo |
| --- | --- |
| `<server_name> <database_name> Event Count` | generic_data |
| `<server_name> <database_name> Status` | generic_data_string |

#### Gateways

Un conjunto por gateway. `<gateway>` es el nombre del gateway.

| Módulo | Tipo |
| --- | --- |
| `<gateway> Active Connection Count` | generic_data |
| `<gateway> Blast Connection Count` | generic_data |
| `<gateway> Last Updated Timestamp` | generic_data |
| `<gateway> PCOIP Connection Count` | generic_data |
| `<gateway> Status` | generic_data_string |

#### Usage Metrics

| Módulo | Tipo |
| --- | --- |
| `Usage Metrics Current Concurrent Application Sessions` | generic_data |
| `Usage Metrics Current Collaborative Sessions` | generic_data |
| `Usage Metrics Current Full VM Sessions` | generic_data |
| `Usage Metrics Current Unmanaged VM Sessions` | generic_data |
| `Usage Metrics Total Collaborators` | generic_data |
| `Usage Metrics Total Concurrent Connections` | generic_data |
| `Usage Metrics Total Concurrent Sessions` | generic_data |
| `Usage Metrics Total Named Users` | generic_data |
| `Usage Metrics Highest Concurrent Application Sessions` | generic_data |
| `Usage Metrics Highest Collaborative Sessions` | generic_data |
| `Usage Metrics Highest Full VM Sessions` | generic_data |
| `Usage Metrics Highest Unmanaged VM Sessions` | generic_data |
| `Usage Metrics Highest Total Collaborators` | generic_data |
| `Usage Metrics Highest Total Concurrent Connections` | generic_data |
| `Usage Metrics Highest Total Concurrent Sessions` | generic_data |
| `Usage Metrics Highest Total Named Users` | generic_data |

#### System Metrics

| Módulo | Tipo |
| --- | --- |
| `System Metrics Event Error Count` | generic_data |
| `System Metrics Event Warning Count` | generic_data |
| `System Metrics Health Metrics Component` | generic_data_string |
| `System Metrics Health Metrics Error Count` | generic_data |
| `System Metrics Health Metrics Healthy Count` | generic_data |
| `System Metrics Health Metrics Total Count` | generic_data |
| `System Metrics Health Metrics Unknown Count` | generic_data |
| `System Metrics Health Metrics Warning Count` | generic_data |
| `System Metrics Problem RDS Hosts Count` | generic_data |
| `System Metrics Problem vCenter VMs Count` | generic_data |
| `System Metrics Sessions Count` | generic_data |

#### Virtual Datacenters

Un conjunto por centro de datos virtual. `<vc>` es el nombre del centro de datos virtual, `<host>` un host, `<datastore>` un datastore y `<server>` un servidor de conexión.

| Módulo | Tipo |
| --- | --- |
| `<vc> Connection Server <server> Server Status` | generic_data_string |
| `<vc> Datastore <datastore> Path` | generic_data_string |
| `<vc> Datastore <datastore> URL` | generic_data_string |
| `<vc> Datastore <datastore> Capacity MB` | generic_data |
| `<vc> Datastore <datastore> Free Space MB` | generic_data |
| `<vc> Datastore <datastore> Status` | generic_data_string |
| `<vc> Host <host> Cluster Name` | generic_data_string |
| `<vc> Host <host> CPU Core Count` | generic_data |
| `<vc> Host <host> CPU MHz` | generic_data |
| `<vc> Host <host> Memory Size MB` | generic_data |
| `<vc> Host <host> Overall CPU Usage MHz` | generic_data |
| `<vc> Host <host> Overall Memory Usage MB` | generic_data |
| `<vc> Host <host> Status` | generic_data_string |
| `<vc> Desktop Pools and Farms Count` | generic_data |

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| Nombre corto de la aplicación | `pandorafms.horizon` |
| Versión del plugin | `1.2` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
