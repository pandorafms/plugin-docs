# Discovery de Proxmox

*Última actualización del artículo: 2026-09-28.*

## Qué monitoriza

El plugin de Discovery de Proxmox se conecta a un clúster de Proxmox VE a través de la API de Proxmox VE y descubre sus recursos. Genera un agente de Pandora FMS por cada recurso descubierto y lo completa con módulos de disponibilidad, capacidad, configuración y rendimiento leídos de la API de Proxmox.

El plugin genera agentes para:

- cada nodo de Proxmox;
- cada máquina virtual QEMU;
- cada contenedor LXC;
- cada almacenamiento definido en un nodo;
- un agente de clúster para las copias de seguridad programadas;
- un agente de centro de datos con el resumen del clúster.

Las categorías de recursos se seleccionan en la tarea y una lista de entidades por tarea permite ajustar qué recursos se monitorizan y renombrar los agentes resultantes.

El plugin se ejecuta como una tarea de Discovery: la consola crea la tarea, el servidor de Discovery ejecuta el plugin y los agentes y módulos generados se crean automáticamente. La tarea entrega los datos de los agentes generados a través de Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.6.1` (`pandorafms.proxmox`) | Objetivo documentado | La versión que describe esta página, identificada por la definición del paquete. |
| Clúster de Proxmox VE con la API accesible en el puerto configurado (por defecto `8006`) | `Required` | El plugin se autentica y lee cada recurso a través de la API de Proxmox VE. |
| Una cuenta o token de API con acceso de lectura a nodos, invitados, almacenamiento, copias de seguridad y estado del clúster | `Required` | El plugin lista nodos, invitados QEMU y LXC, almacenamiento y copias de seguridad del clúster; nunca cambia la configuración de Proxmox. |
| Una versión concreta de Proxmox VE | `Not validated` | Ningún registro de pruebas publicado establece compatibilidad con una versión concreta de Proxmox VE. |
| Sistema operativo del host que ejecuta el plugin | `Not validated` | Ningún registro de pruebas publicado establece compatibilidad con un sistema operativo. |

### Requisitos

- Un servidor de Pandora FMS con Discovery habilitado para ejecutar la tarea, y una consola para definirla.
- Un endpoint de Proxmox VE accesible desde el servidor de Discovery, con la API expuesta en el puerto configurado. El puerto por defecto de la API de Proxmox VE es `8006`.
- Una de estas credenciales:
    - un usuario de Proxmox en formato `user@realm`, por ejemplo `root@pam`, con su contraseña;
    - un token de API de Proxmox, indicado mediante su nombre de token y su secreto.
- Un grupo de agentes de destino y un intervalo de monitorización para los agentes generados. Ambos proceden de la tarea de Discovery y los hereda cada agente generado.
- Conectividad de red con el destino Tentacle, porque la tarea transfiere los datos de los agentes generados a través de Tentacle.
- Una ruta escribible para el archivo de lista de entidades. Por defecto es un archivo específico de la tarea de Discovery dentro del directorio temporal de Pandora.
- El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que el servidor de Discovery ejecuta en el servidor de Pandora FMS.

Concede a la cuenta o al token de Proxmox únicamente el acceso de lectura que necesite tu monitorización. El plugin solo consulta la API; nunca modifica nodos, invitados, almacenamiento ni copias de seguridad.

El plugin se conecta a la API de Proxmox VE sin verificar su certificado TLS. Ejecuta la tarea solo en una red de confianza o protege el tráfico mediante un túnel. Este plugin no ofrece ninguna opción para habilitar la verificación del certificado.

### Instalar el plugin

Carga el paquete `.disco` desde **Management → Discovery → Manage disco packages**: elige **Select a file**, selecciona el paquete y pulsa **Upload DISCO**. Tras la carga, **Proxmox** aparece en la lista de paquetes y en la sección **Applications** del asistente de Discovery.

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Applications → Proxmox**. El asistente recorre la definición genérica de la tarea y dos pasos del plugin: **Proxmox base** y **Proxmox detailed**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Definición de la tarea

El paso genérico pide el **nombre** de la tarea, el **grupo de agentes** y el **servidor** en el que se ejecuta, y el **intervalo**. El grupo y el intervalo se pasan al plugin y los hereda cada agente generado.

### Paso 2 — Proxmox base

Datos de conexión, autenticación y destino Tentacle:

- **Proxmox host** es la dirección o el nombre de host del endpoint de Proxmox VE.
- **Port** es el puerto de la API. Por defecto `8006`.
- **Proxmox user** es la cuenta en formato `user@realm`, por ejemplo `root@pam`.
- **Password Authentication** controla la visibilidad de **Password**. Introduce la contraseña del usuario de Proxmox.
- **Token API Authentication** controla la visibilidad de **Token Name** y **Token Password**. Introduce el nombre y el secreto de un token de API de Proxmox.
- **Tentacle IP**, **Tentacle port**, **Tentacle client path** y **Tentacle extra options** definen cómo se envían los datos generados. Deja los valores por defecto salvo que tu entorno necesite otro destino Tentacle.
- **Agent name prefix** se antepone a los nombres de los agentes generados. Por defecto `Proxmox.`.
- **Agent autodisable mode** crea los agentes generados en modo autodisable.

Las dos casillas de autenticación solo controlan qué campos muestra el asistente. El plugin se autentica con el token de API cuando **Token Name** y **Token Password** están ambos informados, y con el usuario y la contraseña de Proxmox en caso contrario. No rellenes solo uno de los campos de token: en ese caso el plugin recurre a la autenticación por contraseña.

![Paso Proxmox base del asistente de Discovery](../assets/images/discovery/proxmox/proxmox-base.png)

### Paso 3 — Proxmox detailed

Categorías de recursos, la lista de entidades y el comportamiento del reescaneo:

- **Scan VMs**, **Scan LXC**, **Scan backups**, **Scan nodes**, **Scan data center** y **Scan storage** habilitan o deshabilitan cada categoría de recurso. Todas están habilitadas por defecto.
- **Entities list file** es la ruta del archivo editable que selecciona y renombra recursos. Consulta [Archivo de lista de entidades](#archivo-de-lista-de-entidades).
- **Enable entities list re-scan interval** reconstruye las secciones de recursos de la lista de entidades tras el intervalo configurado. Consulta [Archivo de lista de entidades](#archivo-de-lista-de-entidades) para conocer sus consecuencias.
- **Re-scan entities list interval** es la frecuencia con la que se reconstruye la lista. Solo se muestra cuando **Enable entities list re-scan interval** está activado.

![Paso Proxmox detailed del asistente de Discovery](../assets/images/discovery/proxmox/proxmox-detailed.png)

## Verificar la primera ejecución

Ejecuta la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea** informa del número total de agentes generados y de cuántos pertenecen a cada grupo de recursos.
2. **Los agentes.** Espera un agente por cada recurso habilitado y accesible, más el agente de copias de seguridad del clúster y el agente de centro de datos cuando sus categorías estén habilitadas.
3. **Los módulos.** Cada agente generado incluye los módulos de su tipo de recurso; un entorno accesible rellena los valores de disponibilidad, capacidad y rendimiento.
4. **La información de ejecución.** Una ejecución correcta no informa de errores; cualquier fallo por recurso se registra ahí.

![Resumen de ejecución de la tarea](../assets/images/discovery/proxmox/task-summary.png)

Si la tarea falla antes de generar nada, el host de Proxmox, el puerto y las credenciales son lo primero que hay que revisar.

## Entender los resultados

### Agentes e identidad

El plugin crea un agente por cada recurso descubierto. Todos los agentes generados pertenecen al grupo de agentes de la tarea y heredan su intervalo. Los agentes de nodo, máquina virtual y LXC también incluyen un campo personalizado, `proxmox_device`, cuyo valor es `Node`, `VM` o `LXC`.

Cada agente tiene un nombre interno estable y un alias legible. El nombre interno es un hash acotado a la tarea de Discovery, al host y puerto de Proxmox, al tipo de recurso y al identificador del recurso. El alias se construye a partir del prefijo configurado y de la identidad del recurso, y puede reescribirse con una regla de renombrado.

| Recurso | Plantilla de alias (por defecto) | Alcance |
| --- | --- | --- |
| Nodo | `<prefix>.<node>.<node id>` | Un agente por nodo |
| Máquina virtual | `<prefix>.<vm name>.<vmid>.<node>` | Un agente por invitado QEMU |
| Contenedor LXC | `<prefix>.<container name>.<vmid>.<node>` | Un agente por invitado LXC |
| Almacenamiento | `<prefix>_<storage>_<node>` | Un agente por almacenamiento de nodo |
| Copias de seguridad | `<prefix>_Backups` | Un agente para todo el clúster |
| Centro de datos | `<prefix>_Data_Center` | Un agente para todo el clúster |

![Agentes generados](../assets/images/discovery/proxmox/generated-agents.png)

Como el nombre interno incluye el identificador de la tarea de Discovery y el endpoint de Proxmox, dos tareas que monitorizan entornos de Proxmox distintos no pueden actualizar el mismo agente aunque coincidan los nombres de sus recursos. El nombre del archivo de lista de entidades también es específico de la tarea.

Las reglas de renombrado solo cambian el alias visible. El nombre interno no se ve afectado y los agentes invitados se identifican por su VMID, así que renombrar un invitado sigue actualizando el mismo agente.

### Archivo de lista de entidades

En su primera ejecución, el plugin crea el archivo de lista de entidades con un encabezado de sección por tipo de recurso y los recursos que ha descubierto:

```text
Node
pve1
VM
pve1/100
LXC
pve1/200
Storage
pve1/local
Backups
Backups
Datacenter
Data_Center
Rename
web-prod TO Production web
```

Elimina una línea de recurso para excluirlo de la monitorización. Los cambios surten efecto en la siguiente ejecución de la tarea. Consulta [Archivo de lista de entidades](#archivo-de-lista-de-entidades) en la referencia para conocer la semántica exacta y el comportamiento del reescaneo.

### Módulos por agente

Cada agente recibe los módulos de su tipo de recurso. Los valores de los módulos se leen de la API de Proxmox en cada ejecución de la tarea; el nombre y la unidad exactos de cada módulo se listan en [Módulos generados](#modulos-generados).

| Agente | Módulos que incluye |
| --- | --- |
| Nodo | Estado y situación del host, CPU, memoria, disco, capacidad de almacenamiento, versión de kernel y del gestor, huella SSL y tráfico de red |
| Máquina virtual | Estado de encendido y situación, uso de CPU, memoria, disco y red |
| Contenedor LXC | Estado de encendido y situación, uso de CPU, memoria, disco y red, más porcentajes de uso relativos al contenedor y al host |
| Almacenamiento | Porcentaje de espacio usado, estado habilitado y activo, capacidad total y usada, tipo, ruta y tipos de contenido |
| Copias de seguridad | Un par de módulos por cada trabajo de copia programado: su estado y el tiempo restante hasta la próxima ejecución |
| Centro de datos | Contadores de nodos, máquinas virtuales y LXC y porcentajes generales de uso de CPU, memoria y almacenamiento |

![Módulos del centro de datos](../assets/images/discovery/proxmox/data-center-modules.png)

## Operar

### Ejecución manual

El plugin también puede ejecutarse fuera del asistente de Discovery con un archivo de configuración. Esto es útil para probar la conectividad, para una ejecución puntual o para una programación propia. El archivo de configuración es una lista simple de líneas `clave=valor`:

```bash
pandora_proxmox --conf <ruta del archivo de configuración>
```

Un archivo de configuración mínimo para una ejecución manual tiene este aspecto:

```text
host=<PROXMOX_HOST>
port=8006
user=<PROXMOX_USER>
password=<PROXMOX_PASSWORD>
prefix=Proxmox.
interval=300
transfer_mode=tentacle
tentacle_ip=<TENTACLE_IP>
tentacle_port=41121
entities_list=/tmp/proxmox_entities_list.txt
```

Todas las claves se documentan en [Archivo de configuración](#archivo-de-configuracion). Cuando no se indica `task_id`, las ejecuciones manuales recurren a la identidad del endpoint para los nombres internos de los agentes.

### Limitaciones

- El plugin no verifica el certificado TLS de Proxmox VE.
- La tarea escribe las credenciales de conexión en su archivo de configuración en el servidor de Pandora FMS. Este plugin no ofrece cifrado de contraseña, así que protege el acceso al servidor y a sus archivos temporales.
- Las copias de seguridad se leen a nivel de clúster. Solo se informan los trabajos de copia de seguridad programados del clúster; la retención de copias por invitado no la expone este plugin.
- El descubrimiento de almacenamiento empareja la lista de almacenamientos de un nodo con la lista de almacenamientos del clúster. Si un nodo informa de un número de almacenamientos distinto al de la lista del clúster, se omite el almacenamiento de ese nodo.
- La lista de entidades solo excluye o renombra recursos. Eliminar un recurso de Proxmox no borra su agente automáticamente.

## Resolución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La tarea informa de un error al iniciar sesión en el entorno de Proxmox | Confirma **Proxmox host** y **Port**, que la API es accesible desde el servidor de Discovery y que las credenciales son válidas. |
| La autenticación falla con una cuenta por contraseña | El usuario de Proxmox debe usar el formato `user@realm`, por ejemplo `root@pam`. |
| No se usa la autenticación por token | Rellena **Token Name** y **Token Password**. Con solo uno de ellos informado, el plugin recurre al usuario y la contraseña. |
| No se genera ningún agente | Confirma las credenciales, que el clúster de Proxmox tiene los recursos que esperas y que las opciones **Scan** correspondientes están habilitadas. |
| Faltan recursos esperados | Revisa el archivo de lista de entidades: una línea eliminada excluye el recurso, y una categoría deshabilitada no se escribe cuando la lista se crea por primera vez. |
| Un agente renombrado no se actualiza | Usa en la regla de renombrado el alias original, el nombre del recurso o el identificador del recurso, y confirma que la regla está en la sección `Rename`. |
| Faltan agentes de almacenamiento en un nodo | El plugin omite un nodo cuya lista de almacenamientos no coincide con la lista del clúster. Confirma que el nodo informa correctamente de sus almacenamientos. |
| Aparecieron agentes nuevos tras actualizar el plugin | La versión `1.6.1` cambió la identidad interna de los agentes. Su primera ejecución crea agentes nuevos en lugar de actualizar los creados por versiones anteriores. Revisa las alertas y paneles que hagan referencia a los agentes antiguos antes de eliminarlos. |
| La transferencia por Tentacle falla | Confirma que el servidor de Discovery puede alcanzar **Tentacle IP** en **Tentacle port** y que el cliente Tentacle está disponible, o define **Tentacle client path**. |

## Referencia

### Parámetros de la tarea

La consola muestra estos campos después de la definición genérica de la tarea. La columna de macro es el identificador usado en la configuración de la tarea generada.

#### Proxmox base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Proxmox host | `_proxmoxHost_` | string | — | Dirección o nombre de host del endpoint de Proxmox VE. Obligatorio |
| Port | `_proxmoxPort_` | number | `8006` | Puerto de la API de Proxmox VE |
| Proxmox user | `_proxmoxUser_` | string | — | Cuenta en formato `user@realm`, por ejemplo `root@pam` |
| Password Authentication | `_passwordAuth_` | checkbox | off | Controla la visibilidad del campo de contraseña |
| Password | `_proxmoxPassword_` | password | — | Contraseña del usuario de Proxmox |
| Token API Authentication | `_TokenAuth_` | checkbox | off | Controla la visibilidad de los campos de token |
| Token Name | `_proxmoxTokenName_` | string | — | Nombre del token de API de Proxmox |
| Token Password | `_proxmoxTokenPassword_` | password | — | Secreto del token de API de Proxmox |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Destino de la transferencia por Tentacle |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de destino de la transferencia por Tentacle |
| Tentacle client path | `_tentaclePath_` | string | — | Ruta opcional al cliente Tentacle cuando no está en el `PATH` por defecto |
| Tentacle extra options | `_tentacleExtraOpt_` | string | — | Opciones adicionales pasadas al cliente Tentacle |
| Agent name prefix | `_prefix_` | string | `Proxmox.` | Se antepone a los alias de los agentes generados |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes generados en modo autodisable |

#### Proxmox detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Scan VMs | `_scanVM_` | checkbox | on | Genera un agente por máquina virtual QEMU |
| Scan LXC | `_scanLXC_` | checkbox | on | Genera un agente por contenedor LXC |
| Scan backups | `_scanBackups_` | checkbox | on | Genera el agente de copias de seguridad del clúster |
| Scan nodes | `_scanNodes_` | checkbox | on | Genera un agente por nodo |
| Scan data center | `_scanDataCenter_` | checkbox | on | Genera el agente de centro de datos |
| Scan storage | `_scanStorage_` | checkbox | on | Genera un agente por almacenamiento de nodo |
| Entities list file | `_entitiesList_` | string | Archivo específico de la tarea en el directorio temporal de Pandora | Archivo editable que selecciona y renombra recursos |
| Enable entities list re-scan interval | `_enableEntitiesInterval_` | checkbox | off | Reconstruye las secciones de recursos tras el intervalo |
| Re-scan entities list interval | `_entitiesInterval_` | select (interval) | `86400` | Intervalo de reconstrucción en segundos. Solo se muestra cuando el reescaneo está habilitado |

La tarea siempre entrega los datos a través de Tentacle con la **Tentacle IP** y el **Tentacle port** configurados; el asistente no ofrece un modo de transferencia local.

### Archivo de configuración

La tarea de Discovery genera un archivo de configuración para el plugin. Se usa el mismo formato en una ejecución manual. Es un archivo de texto plano de líneas `clave=valor`. Esta es la superficie de configuración de todos los parámetros.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `host` | — | Dirección o nombre de host de Proxmox VE. Obligatorio |
| `port` | `8006` | Puerto de la API de Proxmox VE |
| `user` | — | Cuenta de Proxmox en formato `user@realm` |
| `password` | — | Contraseña del usuario de Proxmox |
| `proxmox_token_name` | — | Nombre del token de API de Proxmox |
| `proxmox_token_pass` | — | Secreto del token de API de Proxmox |
| `prefix` | `Proxmox.` | Prefijo de los alias de los agentes generados |
| `agents_group_name` | — | Grupo de agentes de los agentes generados |
| `interval` | `300` | Intervalo de los agentes generados |
| `task_id` | — | Identificador de la tarea de Discovery. Acota los nombres internos de los agentes |
| `agent_autodisable` | `False` | Ponlo a `true` para crear los agentes generados en modo autodisable |
| `scan_nodes` | `1` | Genera un agente por nodo |
| `scan_backups` | `1` | Genera el agente de copias de seguridad del clúster |
| `scan_vms` | `1` | Genera un agente por máquina virtual QEMU |
| `scan_lxc` | `1` | Genera un agente por contenedor LXC |
| `scan_data_center` | `1` | Genera el agente de centro de datos |
| `scan_storage` | `1` | Genera un agente por almacenamiento de nodo |
| `discard_nodes` | `[]` | Lista JSON de nombres de nodo que se descartan de la monitorización de nodos, invitados y almacenamiento |
| `entities_list` | `/tmp/proxmox_entities_list.txt` | Ruta del archivo de lista de entidades |
| `enable_entities_interval` | `False` | Ponlo a `true` para reconstruir la lista de entidades por intervalos |
| `entities_interval` | `86400` | Intervalo de reconstrucción en segundos |
| `transfer_mode` | `tentacle` | `tentacle` envía los datos por Tentacle; `local` los escribe en `local_folder` |
| `tentacle_ip` | `127.0.0.1` | Dirección de destino Tentacle |
| `tentacle_port` | `41121` | Puerto de destino Tentacle |
| `tentacle_path` | — | Ruta opcional al cliente Tentacle |
| `tentacle_opts` | — | Opciones adicionales pasadas al cliente Tentacle |
| `temporal` | `/tmp/` | Carpeta de trabajo para archivos temporales |
| `local_folder` | `/var/spool/pandora/data_in/` | Carpeta de destino cuando `transfer_mode` es `local` |
| `pandora_url` | — | URL de la API de la consola |
| `api_user` | — | Usuario de la API de la consola |
| `api_pass` | — | Contraseña de la API de la consola |
| `apiuser_pass` | — | Contraseña del usuario de la API de la consola |

Los parámetros de la API de la consola se usan para crear el campo personalizado `proxmox_device` en Pandora FMS cuando todavía no existe.

### Archivo de lista de entidades

La lista de entidades es un archivo de texto plano que selecciona y renombra recursos. El plugin lo crea en la primera ejecución y lo lee en cada ejecución.

| Sección | Formato de entrada | Ejemplo |
| --- | --- | --- |
| `Node` | Nombre del nodo | `pve1` |
| `VM` | `<node>/<vmid>` | `pve1/100` |
| `LXC` | `<node>/<vmid>` | `pve1/200` |
| `Storage` | `<node>/<storage>` | `pve1/local` |
| `Backups` | La entrada fija `Backups` | `Backups` |
| `Datacenter` | La entrada fija `Data_Center` | `Data_Center` |
| `Rename` | `ORIGINAL TO NEW` | `web-prod TO Production web` |

Reglas:

- Elimina una línea de recurso para excluirlo de la monitorización. Los cambios surten efecto en la siguiente ejecución de la tarea.
- La entrada `all` dentro de una sección permite todos los recursos actuales de ese tipo.
- Las categorías de escaneo deshabilitadas no se escriben cuando la lista se crea por primera vez. Habilita un intervalo o añade entradas manualmente si habilitas una categoría más adelante.
- **Enable entities list re-scan interval** reconstruye las secciones de recursos tras el intervalo configurado. Está desactivado por defecto para que las exclusiones manuales persistan. Una reconstrucción descubre recursos nuevos y conserva las reglas `Rename`, pero restaura las líneas de recurso que habías eliminado.
- El archivo debe ser escribible por la cuenta que ejecuta la tarea de Discovery.

### Reglas de renombrado

Añade asignaciones en la sección `Rename` con el formato `ORIGINAL TO NEW`.

- `ORIGINAL` puede ser el alias original del agente incluido el prefijo, o el nombre del recurso de origen, por ejemplo `web-prod`.
- El destino se convierte en el alias visible del agente.
- El renombrado no cambia el nombre interno hasheado del agente. Los agentes invitados se identifican por su VMID.
- Para nombres de recurso iguales en nodos distintos, usa el alias original completo para dirigirte a un solo agente.

### Módulos generados

Las siguientes tablas listan los módulos que genera el plugin por recurso.

#### Nodos

En los nombres de módulo, `<node>` es el nombre del nodo. Los módulos se generan solo cuando la API de Proxmox devuelve el campo correspondiente.

| Nombre del módulo | Tipo | Unidad | Descripción |
| --- | --- | --- | --- |
| `<node>_maxdisk` | generic_data | Bytes | Tamaño del disco raíz |
| `<node>_uptime` | generic_data | — | Tiempo de actividad |
| `<node>_status` | generic_proc | — | `1` cuando el nodo está online, `0` en caso contrario |
| `<node>_state` | generic_data_string | — | Estado del nodo informado por la API |
| `<node>_maxcpu` | generic_data | — | Número máximo de CPU |
| `<node>_disk` | generic_data | Bytes | Uso de disco |
| `<node>_mem` | generic_data | Bytes | Uso de memoria |
| `<node>_maxmem` | generic_data | Bytes | Memoria máxima |
| `<node>_cpu` | generic_data | % | Uso de CPU, con el modelo de CPU y el número de núcleos en la descripción |
| `<node>_ssl_fingerprint` | generic_data_string | — | Huella SSL |
| `<node>_mem_usage_pct` | generic_data | % | Porcentaje de uso de memoria |
| `<node>_disk_usage_pct` | generic_data | % | Porcentaje de uso de disco |
| `<node>_kernel_version` | generic_data_string | — | Versión del kernel |
| `<node>_manager_version` | generic_data_string | — | Versión del gestor de Proxmox |
| `<node>_netin_traffic` | generic_data | bytes/s | Tráfico de red entrante |
| `<node>_netout_traffic` | generic_data | bytes/s | Tráfico de red saliente |

#### Máquinas virtuales

En los nombres de módulo, `<vm>` es el nombre de la máquina virtual. Los módulos se generan solo cuando la API de Proxmox devuelve el campo correspondiente.

| Nombre del módulo | Tipo | Unidad | Descripción |
| --- | --- | --- | --- |
| `<vm>_Status` | generic_proc | — | `1` cuando el invitado está en ejecución, `0` en caso contrario |
| `<vm>_State` | generic_data_string | — | Estado del invitado informado por la API |
| `<vm>_netout` | generic_data | — | Tráfico de red saliente |
| `<vm>_diskread` | generic_data | — | Lectura de disco |
| `<vm>_cpu` | generic_data | % | Uso de CPU |
| `<vm>_disk` | generic_data | Bytes | Uso de disco |
| `<vm>_mem` | generic_data | — | Uso de memoria en bytes |
| `<vm>_netin` | generic_data | — | Tráfico de red entrante |
| `<vm>_uptime` | generic_data | — | Tiempo de actividad |
| `<vm>_maxmem` | generic_data | bytes | Memoria máxima |
| `<vm>_maxdisk` | generic_data | bytes | Tamaño del disco raíz |
| `<vm>_diskwrite` | generic_data | — | Escritura de disco |
| `<vm>_cpus` | generic_data | — | CPUs máximas utilizables |

#### Contenedores LXC

Un contenedor LXC genera los mismos módulos que una máquina virtual, con el nombre del contenedor como `<lxc>`, más los siguientes módulos de porcentaje.

| Nombre del módulo | Tipo | Unidad | Descripción |
| --- | --- | --- | --- |
| `<lxc>_cpu_usage_host_pct` | generic_data | % | Uso de CPU del contenedor relativo al total de núcleos del host |
| `<lxc>_mem_usage_pct` | generic_data | % | Porcentaje de uso de memoria del contenedor |
| `<lxc>_mem_usage_host_pct` | generic_data | % | Uso de memoria del contenedor relativo a la memoria total del host |

#### Almacenamiento

En los nombres de módulo, `<node>` es el nombre del nodo y `<storage>` es el nombre del almacenamiento.

| Nombre del módulo | Tipo | Unidad | Descripción |
| --- | --- | --- | --- |
| `<node>_<storage>_disk_usage_pct` | generic_data | % | Porcentaje de espacio usado |
| `<node>_<storage>_enable` | generic_proc | — | `1` cuando el almacenamiento está habilitado, `0` en caso contrario |
| `<node>_<storage>_is_active` | generic_proc | — | `1` cuando el almacenamiento está activo, `0` en caso contrario |
| `<node>_<storage>_total_capacity` | generic_data | bytes | Capacidad total de disco |
| `<node>_<storage>_used_space` | generic_data | bytes | Espacio de disco usado |
| `<node>_<storage>_type` | generic_data_string | — | Tipo de almacenamiento |
| `<node>_<storage>_path` | generic_data_string | — | Ruta del almacenamiento |
| `<node>_<storage>_content` | generic_data_string | — | Tipos de contenido admitidos por el almacenamiento, como lista |

#### Copias de seguridad

El agente de copias de seguridad del clúster genera un par de módulos por cada trabajo de copia programado. En los nombres de módulo, `<vmid>` y `<node>` proceden del trabajo de copia; son `None` cuando la API no los devuelve.

| Nombre del módulo | Tipo | Unidad | Descripción |
| --- | --- | --- | --- |
| `<vmid>_<node>info` | generic_data_string | — | `enabled` o `disabled`. La descripción incluye la próxima ejecución, la programación, el almacenamiento, el ID de copia y los valores repeat-missed |
| `<vmid>_<node>_next_backup` | generic_data | s | Tiempo restante hasta la próxima copia de seguridad |

![Módulos de copias de seguridad](../assets/images/discovery/proxmox/backups-modules.png)

#### Centro de datos

El agente de centro de datos incluye el resumen del clúster.

| Nombre del módulo | Tipo | Unidad | Descripción |
| --- | --- | --- | --- |
| `data_center_status` | generic_data_string | — | `OK` cuando ningún nodo está offline, `Offline Nodes` en caso contrario |
| `data_center_nodes_online` | generic_data | — | Número de nodos online |
| `data_center_nodes_offline` | generic_data | — | Número de nodos offline |
| `data_center_total_nodes` | generic_data | — | Número total de nodos |
| `data_center_total_vm` | generic_data | — | Número total de máquinas virtuales |
| `data_center_vm_running` | generic_data | — | Número de máquinas virtuales en ejecución |
| `data_center_vm_stopped` | generic_data | — | Número de máquinas virtuales detenidas |
| `data_center_total_lxc` | generic_data | — | Número total de contenedores LXC |
| `data_center_lxc_running` | generic_data | — | Número de contenedores LXC en ejecución |
| `data_center_lxc_stopped` | generic_data | — | Número de contenedores LXC detenidos |
| `data_center_cpu_usage_pct` | generic_data | % | Uso general de CPU |
| `data_center_mem_usage_pct` | generic_data | % | Uso general de memoria |
| `data_center_storage_usage_pct` | generic_data | % | Uso general de almacenamiento |
