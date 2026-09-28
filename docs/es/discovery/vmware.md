# Discovery de VMware

*Última actualización del artículo: 2026-09-15.*

## Qué monitoriza

El plugin de Discovery de VMware se conecta a un servidor VMware vCenter a través de la API de vSphere y descubre los recursos de un datacenter. Genera un agente de Pandora FMS por cada recurso descubierto y lo completa con módulos de disponibilidad, capacidad, configuración y rendimiento leídos de vCenter.

El plugin genera agentes para:

- el propio datacenter;
- cada host ESXi del datacenter;
- cada datastore;
- cada máquina virtual, incluidas las que están anidadas en carpetas de VMware;
- cada resource pool, cuando **Scan Resource Pools** está activado;
- opcionalmente, un agente por cada switch virtual (vSwitch) de cada host ESXi cuando se activa **Virtual network monitoring**.

Cuando se activa **Event mode**, el plugin también lee los eventos de vCenter y los reenvía a la consola de eventos de Pandora FMS, donde siguen el flujo normal de eventos.

El plugin se ejecuta como una tarea de Discovery: la consola crea la tarea, el servidor de Discovery ejecuta el plugin y los agentes y módulos generados se crean automáticamente. La tarea entrega los datos de los agentes generados a través de Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.21` (`pandorafms.vmware`) | Objetivo documentado | Versión descrita en esta página, identificada por la definición del paquete. |
| VMware vCenter Server con al menos un datacenter | `Requerido` | El plugin resuelve todos los objetos gestionados a través de un contenedor de datacenter y se conecta a un endpoint de vCenter. |
| Una cuenta de vCenter con acceso de lectura al datacenter objetivo | `Requerido` | El plugin se autentica y lee datos de recursos y de rendimiento. Nunca modifica la configuración de vCenter. |
| Una versión concreta de vCenter o ESXi | `Sin validar` | Ningún registro de pruebas publicado establece compatibilidad con una versión concreta de VMware. |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas publicado establece compatibilidad con sistemas operativos. |

### Requisitos

- Un servidor Pandora FMS con Discovery habilitado para ejecutar la tarea y una consola para definirla.
- Un servidor VMware vCenter que exponga la API de vSphere y sea accesible desde el servidor de Discovery. El plugin busca el datacenter por el nombre exacto que muestra vCenter.
- Una cuenta de usuario de vCenter que pueda autenticarse y leer el datacenter, los hosts, los datastores, las máquinas virtuales, los resource pools y los contadores de rendimiento. Concede únicamente los permisos de lectura que requiera tu monitorización.
- Un grupo de agentes de destino y un intervalo de monitorización para los agentes generados. Ambos proceden de la tarea de Discovery y los hereda cada agente generado.
- Accesibilidad de red al destino de Tentacle, porque la tarea transfiere los datos de los agentes generados a través de Tentacle.
- Para **Event mode**, una API de consola de Pandora FMS accesible y credenciales de API válidas. La tarea pasa al plugin el endpoint y las credenciales de la API de consola.
- El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que el servidor de Discovery ejecuta en el servidor Pandora FMS.

### Instalar el plugin

Carga el paquete `.disco` desde **Management → Discovery → Manage disco packages**: elige **Select a file**, selecciona el paquete y haz clic en **Upload DISCO**. Una vez cargado, **VMware** aparece en la lista de paquetes y en la sección **Applications** del asistente de Discovery.

![Gestor de paquetes disco](../assets/images/discovery/vmware/manage-disco-packages.png)

![VMware en las aplicaciones de Discovery](../assets/images/discovery/vmware/applications-vmware.png)

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Applications → VMware**. El asistente recorre la definición genérica de la tarea y tres pasos del plugin: **VMware base**, **VMware agents** y **VMware detailed**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Definición de la tarea

El paso genérico solicita el **nombre** de la tarea, el **grupo de agentes** y el **servidor** en el que se ejecuta, y el **intervalo**. El grupo y el intervalo se pasan al plugin y los hereda cada agente generado.

### Paso 2 — VMware base

Datos de conexión y destino de Tentacle:

- **V-Center IP** es la dirección o el nombre de host del servidor vCenter.
- **Datacenter name** debe coincidir exactamente con el nombre del datacenter que aparece en el gestor de VMware.
- **Datacenter user** y **Password** son las credenciales de vCenter.
- **Encrypt passwords** cifra la contraseña antes de almacenarla en la configuración de la tarea.
- **Tentacle IP**, **Tentacle port** y **Tentacle extra options** definen cómo se envían los datos generados. Deja los valores por defecto salvo que tu entorno necesite otro destino de Tentacle.

![Paso VMware base](../assets/images/discovery/vmware/vmware-base.png)

### Paso 3 — VMware agents

Cuando los datos de conexión son válidos, la tarea consulta vCenter y muestra el árbol descubierto: **ESXi**, **Datastores**, **VMs** y **Resource pools**.

- **Monitor exclusive agents**, cuando se activa, limita la tarea a las entidades seleccionadas en el árbol en lugar del escaneo automático. Esta opción tiene prioridad sobre las opciones de escaneo del paso siguiente.
- **Exclusive agents** es el árbol en el que seleccionas las entidades que se van a monitorizar. Marca la casilla situada junto a una entidad, un grupo o la categoría completa para incluirla.

![Paso VMware agents](../assets/images/discovery/vmware/vmware-agents.png)

### Paso 4 — VMware detailed

Comportamiento detallado de la tarea:

- **Max threads** define cuántas entidades se monitorizan de forma concurrente. Aumentarlo reduce el tiempo de ejecución y aumenta el uso de CPU.
- **Autodisabled agents**, cuando se activa, crea los agentes generados en modo autodisabled.
- **Enable re-scan interval** y **Re-scan interval** controlan cada cuánto tiempo el plugin actualiza la lista de entidades para buscar nuevas. El intervalo de re-escaneo no es el intervalo de ejecución de la tarea.
- **Retry send** reintenta el envío por Tentacle cuando falla.
- **Event mode** reenvía los eventos de vCenter a la consola de eventos de Pandora FMS. Solo está disponible para vCenter y requiere que el agente del datacenter exista en Pandora FMS.
- **Virtual network monitoring** genera un agente por cada switch virtual (vSwitch) de cada host ESXi, con módulos por cada port group.
- **Scan datastores**, **Scan datacenters**, **Scan ESXs**, **Scan VMs** y **Scan Resource Pools** habilitan o deshabilitan cada categoría de entidad. Se ignoran para la selección de entidades cuando **Monitor exclusive agents** está activado.
- **Extra settings** es un bloque de configuración en bruto que se añade al archivo de configuración que construye la tarea. Úsalo para opciones que el asistente no expone, por ejemplo un bloque **Rename**. Consulta [Archivo de configuración](#archivo-de-configuracion).

![Paso VMware detailed](../assets/images/discovery/vmware/vmware-detailed.png)

## Verificar la primera ejecución

Ejecuta la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea** muestra el progreso general y un resumen con el nombre del datacenter y el número de ESXs, datastores, VMs y resource pools procesados.
2. **Los agentes.** Espera un agente por cada categoría de entidad habilitada y accesible, más un agente vSwitch por cada host ESXi cuando **Virtual network monitoring** está activado.
3. **Los módulos.** Cada agente generado incorpora los módulos de su entidad; un entorno accesible rellena los valores de disponibilidad, capacidad y rendimiento.
4. **La información de ejecución.** Una ejecución correcta no registra errores; cualquier fallo por entidad se registra ahí.

![Resumen de ejecución de la tarea](../assets/images/discovery/vmware/task-summary.png)

Si la tarea falla antes de generar nada, lo primero que hay que revisar es la dirección de vCenter, el nombre del datacenter y las credenciales.

## Entender los resultados

### Agentes e identidad

El plugin crea un agente por cada entidad descubierta. Todos los agentes generados pertenecen al grupo de la tarea, heredan su intervalo, informan de `VMware` como sistema operativo y llevan campos personalizados con la dirección de vCenter (`vmware_vcenter_ip`), el datacenter (`vmware_datacenter`), el tipo de entidad (`vmware_type`) y, cuando lo tienen, su agente padre (`vmware_parent`).

Los nombres de los agentes se construyen a partir del nombre original de la entidad más un prefijo opcional, y cada tipo de entidad tiene su propio padre:

| Entidad | Nombre del agente | Agente padre |
| --- | --- | --- |
| Datacenter | El nombre del datacenter | — |
| Datastore | El identificador de objeto gestionado del datastore por defecto; el nombre del datastore si se configura así | El agente del datacenter |
| Host ESXi | El nombre del host ESXi | El agente del datacenter |
| Máquina virtual | El nombre de la máquina virtual | El agente del host ESXi que la ejecuta |
| Resource pool | El nombre del resource pool | — |
| vSwitch (virtual network monitoring) | `<host ESXi>_<vSwitch>` | El agente del host ESXi |

Los prefijos por tipo de entidad se configuran con el bloque **Header**, y los nombres de entidad se pueden reescribir con el bloque **Rename**; ambos se describen en [Archivo de configuración](#archivo-de-configuracion). Cambiar un prefijo o un renombrado más adelante cambia la identidad del agente generado.

El agente del datacenter es el punto de entrada: el plugin lo busca por nombre cuando **Event mode** crea eventos, así que mantén **Scan datacenters** habilitado (o crea el agente del datacenter por otro medio) antes de depender de los eventos.

Cuando **Enable re-scan interval** está activo, el plugin guarda en caché la lista de entidades descubiertas y solo la actualiza cuando ha transcurrido el **Re-scan interval** configurado. Las entidades nuevas aparecen tras un re-escaneo; las entidades eliminadas de vCenter no se borran automáticamente.

### Módulos por agente

Cada agente recibe los módulos de su tipo de entidad. Los valores de los módulos se leen de vCenter en cada ejecución de la tarea; el nombre exacto y el estado por defecto de cada módulo se listan en [Módulos generados](#modulos-generados).

| Agente | Módulos que incorpora |
| --- | --- |
| Datacenter | Disponibilidad de vCenter: `Ping` y `Check 443 port` |
| Datastore | Capacidad, espacio libre, sobreasignación y estado de rutas del datastore |
| Host ESXi | Módulos de estado, configuración y hardware del host, más módulos de rendimiento de CPU, memoria, disco y red |
| Máquina virtual | Estado de encendido y de las tools, configuración, asignación de recursos, discos, snapshots y módulos de rendimiento |
| Resource pool | Consumo de CPU y memoria, memoria concedida, compartida, swap, balloon y overhead |
| vSwitch | Por cada port group: octetos recibidos/enviados, estado operativo, estado general y número de VMs conectadas |

## Operación

### Ejecución manual

El plugin también se puede ejecutar fuera del asistente de Discovery con un archivo de configuración. Es útil para probar la conectividad, para una ejecución puntual o para una planificación propia. Escribe un archivo de configuración que use al menos el bloque `Configuration` con `server`, `datacenter`, `user` y `pass`, y ejecuta el punto de entrada del plugin pasando el archivo como argumento. Todos los bloques y parámetros se documentan en [Archivo de configuración](#archivo-de-configuracion).

La ejecución manual muestra un único módulo, `VMware Plugin <datacenter>`, de tipo `async_proc`: su valor es `1` cuando la ejecución terminó sin errores y `0` en caso contrario, y su descripción contiene el resumen de ejecución y los posibles errores. Cuando el plugin se ejecuta como tarea de Discovery, esa misma información pasa a ser la información de ejecución de la tarea.

### Monitorización de eventos

Con **Event mode** activado, el plugin lee los eventos de vCenter ocurridos desde la ejecución anterior y los crea en la consola de eventos de Pandora FMS. La ventana temporal comienza en la marca de tiempo guardada por la ejecución anterior y termina en el momento actual, por lo que la primera ejecución solo lee los eventos posteriores al intervalo configurado.

- Los eventos se crean sobre el agente del datacenter, con `VMware` como origen.
- La severidad de vCenter se traduce a la severidad de Pandora FMS: los eventos `error` pasan a crítico, los eventos `warning` pasan a aviso y cualquier otro evento es informativo.
- La correlación de eventos solo está disponible al conectar con vCenter; una conexión que no lo sea no puede devolver eventos.
- Event mode requiere que la API de consola de Pandora FMS sea accesible y que el agente del datacenter exista.

La contraseña indicada en la tarea se cifra con un algoritmo simétrico antes de almacenarse en la configuración de la tarea. Considera esto una ofuscación, no un sustituto del control de acceso: protege la consola de Pandora FMS, su servidor y sus archivos temporales de acuerdo con tu política de seguridad.

## Resolución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La tarea informa de un error al conectar con vCenter | Confirma **V-Center IP** y que el servidor vCenter sea accesible por red desde el servidor de Discovery. |
| La tarea informa de que no se encontró el datacenter | El mensaje enumera los datacenters disponibles. Corrige **Datacenter name** para que coincida exactamente con el nombre de vCenter. |
| No se genera ningún agente | Confirma las credenciales, que el datacenter objetivo tenga las entidades esperadas y que las opciones **Scan** correspondientes estén habilitadas. |
| Faltan entidades esperadas | Revisa **Monitor exclusive agents** y su árbol: cuando está activado, las opciones de escaneo se ignoran y solo se monitorizan las entidades seleccionadas. Comprueba también que haya transcurrido el intervalo de re-escaneo. |
| Event mode informa de que el agente del datacenter no existe | Habilita **Scan datacenters** para que se genere el agente del datacenter y confirma que la API de consola sea accesible con credenciales válidas. |
| Event mode informa de que la correlación de eventos solo está disponible en vCenter | No se pueden leer eventos desde una conexión que no exponga el gestor de eventos de vCenter. |
| Falla el envío por Tentacle | Confirma que el servidor de Discovery puede alcanzar **Tentacle IP** en **Tentacle port** y habilita **Retry send**. |
| La ejecución tarda demasiado | Aumenta **Max threads** para monitorizar más entidades de forma concurrente, teniendo en cuenta el mayor uso de CPU. |

## Referencia

### Parámetros de la tarea

La consola presenta estos campos después de la definición genérica de la tarea. La columna de macro es el identificador que se usa en la configuración generada de la tarea.

#### VMware base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| V-Center IP | `_server_` | string | — | Dirección o nombre de host del servidor vCenter. Obligatorio |
| Datacenter name | `_datacenter_` | string | — | Datacenter que se va a monitorizar. Debe coincidir con el nombre de vCenter. Obligatorio |
| Datacenter user | `_user_` | string | — | Usuario de vCenter. Obligatorio |
| Password | `_pass_` | password | — | Contraseña de vCenter. Obligatoria. Se cifra cuando **Encrypt passwords** está activado |
| Encrypt passwords | `_useEncryptedPassword_` | checkbox | off | Cifra la contraseña almacenada en la configuración de la tarea |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Destino del envío por Tentacle |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de destino del envío por Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | string | — | Opciones adicionales que se pasan al cliente de Tentacle |

#### VMware agents

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Monitor exclusive agents | `_monitorExclusiveAgents_` | checkbox | off | Monitoriza solo las entidades seleccionadas en **Exclusive agents** e ignora las opciones de escaneo |
| Exclusive agents | `_exclusiveAgents_` | tree | — | Árbol de selección. Las entidades elegidas se guardan en `_exclusiveESXi_`, `_exclusiveDatastores_`, `_exclusiveVMs_` y `_exclusiveRP_` |

#### VMware detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `5` | Número de entidades monitorizadas de forma concurrente |
| Autodisabled agents | `_autodisabledAgents_` | checkbox | off | Crea los agentes generados en modo autodisabled |
| Enable re-scan interval | `_enableReconInterval_` | checkbox | on | Habilita la actualización de la lista de entidades |
| Re-scan interval | `_reconInterval_` | select (interval) | `5 minutes` | Cada cuánto se actualiza la lista de entidades. Solo se muestra con **Enable re-scan interval** activado |
| Retry send | `_retrySend_` | checkbox | off | Reintenta el envío por Tentacle si falla |
| Event mode | `_eventMode_` | checkbox | off | Reenvía los eventos de vCenter. Solo para vCenter |
| Virtual network monitoring | `_virtualNetworkMonitoring_` | checkbox | off | Genera un agente por vSwitch |
| Scan datastores | `_scanDatastore_` | checkbox | on | Genera un agente por datastore |
| Scan datacenters | `_scanDatacenter_` | checkbox | on | Genera el agente del datacenter |
| Scan ESXs | `_scanESX_` | checkbox | on | Genera un agente por host ESXi |
| Scan VMs | `_scanVM_` | checkbox | on | Genera un agente por máquina virtual |
| Scan Resource Pools | `_scanRP_` | checkbox | off | Genera un agente por resource pool |
| Extra settings | `_extraSettings_` | textarea | — | Bloque de configuración en bruto que se añade al archivo de configuración generado |

La tarea entrega siempre los datos a través de Tentacle con la **Tentacle IP** y el **Tentacle port** configurados; el asistente no ofrece un modo de transferencia local.

### Archivo de configuración

La tarea de Discovery construye un archivo de configuración para el plugin. Se usa el mismo formato en una ejecución manual. Es un archivo de texto plano de bloques y líneas `clave valor`; las líneas vacías y las que empiezan por `#` se ignoran.

#### Bloque Configuration

Estos parámetros se aplican a toda la ejecución y se leen del bloque `Configuration`.

| Parámetro | Por defecto | Descripción |
| --- | --- | --- |
| `server` | — | Dirección o nombre de host de vCenter. Obligatorio |
| `datacenter` | — | Nombre del datacenter. Obligatorio |
| `user` | — | Usuario de vCenter. Obligatorio |
| `pass` | — | Contraseña de vCenter. Obligatoria |
| `group` | `1` | Grupo de agentes para los agentes generados |
| `interval` | `1` | Intervalo de los agentes generados |
| `use_encrypted_password` | `0` | Ponlo a `1` cuando `pass` esté cifrada |
| `threads` | `4` | Número de entidades monitorizadas de forma concurrente |
| `autodisabled_agents` | `0` | Ponlo a `1` para crear los agentes generados en modo autodisabled |
| `enable_recon_interval` | `1` | Habilita la actualización de la lista de entidades |
| `recon_interval` | `1` | Segundos antes de que la lista de entidades se vuelva a actualizar |
| `scan_datacenter` | `1` | Genera el agente del datacenter |
| `scan_datastore` | `1` | Genera un agente por datastore |
| `scan_esx` | `1` | Genera un agente por host ESXi |
| `scan_vm` | `1` | Genera un agente por máquina virtual |
| `scan_rp` | `0` | Genera un agente por resource pool |
| `monitor_exclusive_agents` | `0` | Monitoriza solo las entidades indicadas en las listas exclusivas |
| `exclusive_esx` | `[]` | Lista JSON de nombres de hosts ESXi que se van a monitorizar |
| `exclusive_datastores` | `[]` | Lista JSON de nombres de datastores que se van a monitorizar |
| `exclusive_vm` | `[]` | Lista JSON de nombres de máquinas virtuales que se van a monitorizar |
| `exclusive_rp` | `[]` | Lista JSON de nombres de resource pools que se van a monitorizar |
| `virtual_network_monitoring` | `0` | Genera un agente por vSwitch |
| `event_mode` | `0` | Reenvía los eventos de vCenter a Pandora FMS |
| `transfer_mode` | `tentacle` | `tentacle` envía los datos por Tentacle; `local` los escribe en `local_folder` |
| `tentacle_ip` | `127.0.0.1` | Dirección de destino de Tentacle |
| `tentacle_port` | `41121` | Puerto de destino de Tentacle |
| `tentacle_opts` | — | Opciones adicionales que se pasan al cliente de Tentacle |
| `local_folder` | `/var/spool/pandora/data_in` | Carpeta de destino cuando `transfer_mode` es `local` |
| `temporal` | `/tmp` | Carpeta de trabajo para archivos temporales |
| `logfile` | `/tmp/vmware_plugin.log` | Archivo de log de la ejecución |
| `entities_list` | `/tmp/vmware_entities_list.txt` | Lista de entidades en caché |
| `event_pointer_file` | `/tmp/vmware_events_pointer.txt` | Marca de tiempo del último evento procesado |
| `retry_send` | `0` | Reintenta el envío por Tentacle si falla |
| `pandora_url` | — | URL de la API de consola, requerida por event mode |
| `api_user` | `admin` | Usuario de la API de consola, requerido por event mode |
| `api_pass` | `1234` | Contraseña de la API de consola, requerida por event mode |
| `apiuser_pass` | `pandora` | Contraseña del usuario de la API de consola, requerida por event mode |
| `verbosity` | `1` | Ponlo a `0` para suprimir los mensajes informativos del log |
| `use_ds_entity_name` | `0` | Ponlo a `1` para nombrar los agentes de datastore con el nombre del datastore en lugar del identificador de objeto gestionado |
| `use_ds_alias_as_name` | `0` | Ponlo a `1` para nombrar los agentes de datastore con el nombre del datastore |
| `flat_datastore_agents` | `0` | Ponlo a `1` para agrupar todos los datastores del datacenter en un único agente |
| `discard_empty_adapters` | `0` | Ponlo a `1` para omitir los adaptadores HBA de ESXi sin targets, dispositivos ni rutas |

#### Bloques de módulos por entidad

La generación de módulos se configura por tipo de entidad dentro de los bloques `Datacenter`, `Datastore`, `ESX` y `VM`. Cada línea dentro de uno de estos bloques empieza por un identificador de módulo seguido de una de estas opciones:

- `enabled` o `disabled` para activar o desactivar un módulo.
- Uno o varios pares `opcion=valor` separados por `;`, que establecen opciones del módulo y lo habilitan.

| Opción | Descripción |
| --- | --- |
| `name` | Nombre del módulo. Usa `%s` para insertar el índice del módulo |
| `desc` | Descripción del módulo |
| `limits_warn` | Límites de aviso, ya sean `min max` o un valor de cadena |
| `limits_crit` | Límites críticos, ya sean `min max` o un valor de cadena |
| `min_warn`, `max_warn`, `str_warning` | Umbrales de aviso |
| `min_crit`, `max_crit`, `str_critical` | Umbrales críticos |
| `min_warn_forced`, `max_warn_forced`, `str_warning_forced` | Umbrales de aviso forzados |
| `min_crit_forced`, `max_crit_forced`, `str_critical_forced` | Umbrales críticos forzados |
| `critical_inverse`, `warning_inverse` | Invierte la dirección del umbral |
| `min`, `max` | Rango permitido del módulo |

Los identificadores de módulo disponibles y su estado por defecto en cada entidad se listan en [Módulos generados](#modulos-generados).

#### Bloques Rename, Reject y Header

- **Rename** reescribe los nombres de entidad antes de que se conviertan en nombres de agente. Cada línea es `<nombre actual> TO <nombre nuevo>`.
- **Reject** excluye entidades por nombre del escaneo. Cada línea es un nombre de entidad. La entrada especial `all_ipaddresses` alterna si el agente del datacenter se crea sin una dirección explícita (por defecto) o asociado a la dirección de vCenter.
- **Header** añade un prefijo a los nombres de los agentes generados. Las entradas válidas son `dc <prefijo>`, `ds <prefijo>`, `esx <prefijo>`, `vm <prefijo>` y `rp <prefijo>`.

#### Contadores de rendimiento personalizados

Se pueden añadir módulos de rendimiento personalizados por tipo de entidad con una línea que empiece por `custom_performance`:

```
custom_performance type=<cpu|mem|disk|net|sys>;metric=<counter>;name=<name>;desc=<description>;limits_warn=<min max>;limits_crit=<min max>
```

Los valores `type` y `metric` identifican el contador de rendimiento de vCenter que se va a leer; el resto de opciones coinciden con las opciones de módulo anteriores.

### Módulos generados

Las tablas siguientes listan los módulos que genera el plugin por entidad. **Por defecto** es el estado en el que se genera el módulo cuando la tarea no lo configura explícitamente.

#### Datacenter

| Clave del módulo | Nombre del módulo | Tipo | Por defecto |
| --- | --- | --- | --- |
| `ping` | `Ping` | generic_proc | on |
| `check443` | `Check 443 port` | generic_proc | on |

#### Datastores

En los nombres de módulo, `<id>` es el identificador de objeto gestionado del datastore por defecto, o el nombre del datastore cuando se configuran las opciones de nombrado de datastores.

| Clave del módulo | Nombre del módulo | Tipo | Unidad | Por defecto |
| --- | --- | --- | --- | --- |
| `capacity` | `CAPACITY - <id>` | generic_data | B | on |
| `freeSpace` | `Free Space - <id>` | generic_data | % | on |
| `freeSpaceBytes` | `Free Space Bytes - <id>` | generic_data | B | on |
| `overallocation` | `Disk Overallocation - <id>` | generic_data | — | on |
| `dsPathStatus` | `ESX-DS Paths Status - <id>` | generic_data | — | on |

#### Hosts ESXi

Estos módulos se generan siempre para un host ESXi conectado y encendido:

| Nombre del módulo | Tipo | Unidad |
| --- | --- | --- |
| `Overall CPU Usage` | generic_data | MHz |
| `Host Alive` | generic_proc | — |
| `Connection State` | generic_data_string | — |
| `Uptime` | generic_data | — |
| `Overall Memory Usage` | generic_data | KB |
| `Boot Time` | generic_data_string | — |
| `SSL Thumbprint` | generic_data_string | — |
| `Power State` | generic_data_string | — |
| `Memory Size` | generic_data | B |

Estos módulos se configuran con una clave de módulo:

| Clave del módulo | Nombre del módulo | Tipo | Unidad | Por defecto |
| --- | --- | --- | --- | --- |
| `cpuUsagePercent` | `CPU Usage` | generic_data | % | on |
| `memoryUsagePercent` | `Memory Usage` | generic_data | % | on |
| `netReceived` | `Data received` | generic_data | KBps | on |
| `netTransmitted` | `Data transmitted` | generic_data | KBps | on |
| `netUsage` | `Net Usage` | generic_data | KBps | on |
| `kernelReadLatency` | `Disk Read Latency` | generic_data | ms | on |
| `kernelWriteLatency` | `Disk Write Latency` | generic_data | ms | on |
| `diskRate` | `Disk Rate` | generic_data | KBps | on |
| `haStatus` | `HA Status` | generic_proc | — | on |
| `pathStatus` | `<nombre de ruta>` | generic_proc | — | on |
| `systemHealthInfoMetrics` | `Sensor <tipo> <nombre>.metric` | generic_data | — | on |
| `cpuInfo` | `CPU Info [<i>]` | generic_data_string | — | off |
| `pciDevice` | `Physical Disk <dispositivo>` | generic_proc | — | off |
| `hbaDevice` | `HBA <dispositivo>` | generic_proc | — | off |
| `pnicInfo` | `PNIC Info <dispositivo>` | generic_data_string | — | off |
| `vnicInfo` | `VNIC Info [<i>]` | generic_data_string | — | off |
| `systemHealthInfo` | `Sensor <tipo> <nombre>` | generic_data | — | off |
| `disksState` | `Disk State <dispositivo>` | generic_proc | — | off |
| `diskRead` | `Disk Read` | generic_data | KBps | off |
| `diskWrite` | `KBps disk write` | generic_data | KBps | off |
| `deviceReadLatency` | `Device Read Latency` | generic_data | ms | off |
| `deviceWriteLatency` | `Device Write Latency` | generic_data | ms | off |
| `netPkgRx` | `Packages Received` | generic_data | Packets | off |
| `netPkgTx` | `Packages Transmitted` | generic_data | Packets | off |
| `maxDiskLatency` | `Max Disk Latency` | generic_data | ms | off |

#### Máquinas virtuales

| Clave del módulo | Nombre del módulo | Tipo | Unidad | Por defecto |
| --- | --- | --- | --- | --- |
| `hostAlive` | `Host Alive` | generic_proc | — | on |
| `cpuUsagePercent` | `CPU Usage` | generic_data | % | on |
| `memoryUsagePercent` | `Memory Usage` | generic_data | % | on |
| `toolsRunningStatus` | `Tools Running Status` | generic_data_string | — | on |
| `diskUsed` | `vDiskUsed <ruta>` | generic_data | % | on |
| `provisioningUsed` | `ProvisioningUsed` | generic_data | % | on |
| `totalReadLatency` | `Disk Read Latency` | generic_data | ms | on |
| `totalWriteLatency` | `Disk Write Latency` | generic_data | ms | on |
| `netReceived` | `Data received` | generic_data | KBps | on |
| `netTransmitted` | `Data transmitted` | generic_data | KBps | on |
| `netUsage` | `Net Usage` | generic_data | KBps | on |
| `haStatus` | `HA Status` | generic_data | — | on |
| `virtualImagePath` | `Virtual Image Path` | generic_data_string | — | off |
| `host` | `Host Info` | generic_data_string | — | off |
| `connectionState` | `Connection State` | generic_data_string | — | off |
| `guestState` | `Guest State` | generic_data_string | — | off |
| `guestOS` | `Guest OS` | generic_data_string | — | off |
| `hostName` | `Host Name` | generic_data_string | — | off |
| `powerState` | `Power State` | generic_data_string | — | off |
| `bootTime` | `Boot Time` | generic_data_string | — | off |
| `vcpuAllocation` | `CPU Allocation - vCPU` | generic_data | CPUs | off |
| `cpuAllocation` | `CPU Allocation` | generic_data_string | — | off |
| `consumedOverheadMemory` | `Consumed Overhead Memory` | generic_data | KB | off |
| `hostMemoryUsage` | `Host Memory Usage` | generic_data | KB | off |
| `maxCpuUsage` | `Max CPU Usage` | generic_data | MHz | off |
| `maxMemoryUsage` | `Max Memory Usage` | generic_data | KB | off |
| `memoryMBAllocation` | `Memory Allocation - MB` | generic_data | MB | off |
| `memoryAllocation` | `Memory Allocation` | generic_data_string | — | off |
| `uptimeSeconds` | `Memory Seconds` | generic_data | s | off |
| `memoryOverhead` | `Memory Overhead` | generic_data | KB | off |
| `overallCpuDemand` | `Overall CPU Demand` | generic_data | MHz | off |
| `overallCpuUsage` | `Overall CPU Usage` | generic_data | MHz | off |
| `privateMemory` | `Private Memory` | generic_data | KB | off |
| `sharedMemory` | `Shared Memory` | generic_data | KB | off |
| `macAddress` | `MAC Address Net [<i>]` | generic_data_string | — | off |
| `ipAddress` | `IP Address [<i>]` | generic_data_string | — | off |
| `snapshotCounter` | `Number Snapshots` | generic_data | — | off |
| `snapshotDate` | `Snapshot Date <nombre>` | generic_data_string | — | off |
| `triggeredAlarmState` | `Trigger Alarm State` | generic_data_string | — | off |
| `diskRead` | `Disk Read` | generic_data | KBps | off |
| `diskWrite` | `Disk Write` | generic_data | KBps | off |
| `netPkgRx` | `Packages Received` | generic_data | Packets | off |
| `netPkgTx` | `Packages Transmitted` | generic_data | Packets | off |
| `diskRate` | `Disk Rate` | generic_data | KBps | off |
| `maxDiskLatency` | `Max Disk Latency` | generic_data | ms | off |
| `heartbeat` | `HeartBeat` | generic_data | — | off |
| `cpuReady` | `CPU Ready` | generic_data | — | off |

#### Resource pools

| Clave del módulo | Nombre del módulo | Tipo | Unidad | Por defecto |
| --- | --- | --- | --- | --- |
| `cpuUsageMhz` | `CPU usage MHz` | generic_data | MHz | on |
| `memActive` | `Active memory` | generic_data | KB | on |
| `memGranted` | `Granted memory` | generic_data | KB | on |
| `memShared` | `Shared memory` | generic_data | KB | on |
| `memSwapped` | `Swapped memory` | generic_data | KB | on |
| `memVmmemctl` | `Balloon memory` | generic_data | KB | on |
| `memOverhead` | `Overhead memory` | generic_data | KB | on |

#### Switches virtuales

Cuando **Virtual network monitoring** está activado, el plugin crea un agente por vSwitch. Por cada port group del vSwitch genera:

| Nombre del módulo | Tipo | Descripción |
| --- | --- | --- |
| `<port group>_ifInOctects` | generic_data | Octetos recibidos |
| `<port group>_ifOutOctects` | generic_data | Octetos enviados |
| `<port group>_ifOperStatus` | generic_proc | Accesibilidad del port group |
| `<port group>_overallStatus` | generic_proc | Estado general del port group |
| `<port group>_connectedVMs` | generic_data | Número de puertos activos |

### Línea de comandos

| Comando | Descripción |
| --- | --- |
| `pandora_vmware <archivo de configuración>` | Ejecuta el plugin con un archivo de configuración |
| `pass_encrypter --Encrypt '<contraseña>'` | Cifra una contraseña para `use_encrypted_password` |
| `pass_encrypter --Decrypt '<contraseña cifrada>'` | Descifra una contraseña generada por el plugin |
