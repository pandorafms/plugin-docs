# OVH Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de OVH monitoriza entornos de OVHcloud a través de la API de OVHcloud. Convierte el resultado en agentes y módulos de Pandora FMS: estado de las instancias de Public Cloud, estadísticas opcionales de CPU, memoria y red por instancia, volúmenes de Public Cloud, servidores dedicados y, opcionalmente, los costes mensuales y totales.

Una tarea de Discovery genera cuatro tipos de agentes:

- **Un agente global** llamado `OVH`, con el número de instancias encontradas y, opcionalmente, los módulos de costes. Se crea en cada ejecución, salvo en enero con **Get monthly and overall costs** activado: en ese mes falla el cálculo de costes del mes anterior y el agente global no se genera.
- **Un agente por cada máquina virtual** (instancia de Public Cloud), con su estado y, opcionalmente, sus estadísticas de rendimiento.
- **Un agente por cada volumen** (volumen de Public Cloud), con su estado, tamaño y asociación.
- **Un agente por cada servidor dedicado**, con su estado y atributos de hardware y ubicación.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.ovh`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Véase [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a la API de OVHcloud | `Requerido` | El addon consulta la API de OVHcloud del endpoint `ovh-eu` |
| Credenciales de la API de OVHcloud (application key, application secret y consumer key) | `Requerido` | Requisito previo, no una declaración de compatibilidad |
| Sistema operativo del servidor de Discovery | `No validado` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `No validado` | No se ha registrado una matriz de versiones para este addon |

El addon se conecta siempre al endpoint `ovh-eu` de la API de OVHcloud. Las cuentas que pertenezcan a otra región de la API de OVHcloud no quedan cubiertas por esta versión.

### Requisitos previos

1. **Conectividad** desde el servidor de Discovery a la API de OVHcloud.
2. **Una application key, un application secret y una consumer key de OVHcloud.** El proceso se describe en la guía de OVHcloud para empezar con su API: [OVHcloud API getting started](https://help.ovhcloud.com/csm/es-es-api-getting-started-ovhcloud-api?id=kb_article_view&sysparm_article=KB0042785).
3. **Pandora FMS**: un servidor de Discovery que ejecute la tarea y la consola que la defina.

### Acceso a la API de OVHcloud

El addon solo realiza peticiones de lectura (`GET`). La consumer key debe estar autorizada para las rutas que corresponden a las opciones que active:

| Ruta | Se usa para |
|------|-------------|
| `/cloud/project` y `/cloud/project/{project}` | Listar los proyectos de Public Cloud (siempre) |
| `/cloud/project/{project}/instance` | Listar las máquinas virtuales (siempre) |
| `/cloud/project/{project}/instance/{instance}/monitoring` | Estadísticas de CPU, memoria y red (con **Advanced statistics** activado) |
| `/cloud/project/{project}/volume` | Volúmenes (con **Scan Volumes** activado) |
| `/dedicated/server` y `/dedicated/server/{server}` | Servidores dedicados (con **Scan Servers** activado) |
| `/me/bill` y `/me/bill/{bill}` | Costes (con **Get monthly and overall costs** activado) |

El application secret y la consumer key son credenciales: no las comparta ni las pegue en tickets o capturas de pantalla.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.ovh](https://marketplace.pandorafms.com/entries/pandorafms.ovh)

Cárguelo en Pandora FMS. Una vez cargado, **OVH** está disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management > Discovery > Cloud** y elija **OVH**. La consola presenta los campos en dos pasos; cada campo se documenta en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **OVH base** — credenciales y destino de los datos de los agentes generados:

    - **OVH application key**, **OVH application secret** y **OVH consumer key**: las credenciales de la API de OVHcloud.
    - **Tentacle IP** y **Tentacle port**: destino de los datos de los agentes generados. Rara vez es necesario cambiarlos.

    ![Paso OVH base del asistente de la tarea de Discovery](../assets/images/discovery/ovh/ovh-task-credentials-tentacle.png)

2. **OVH detailed** — los recursos que se monitorizan:

    - **Scan Volumes**, **Scan Servers** y **Monitor virtual machines**: qué tipos de recurso generan agentes.
    - **Get monthly and overall costs**: añade los módulos de costes al agente global.
    - **Advanced statistics**: solo se muestra con **Monitor virtual machines** activado; añade los módulos de rendimiento a los agentes de máquina virtual.
    - **Autodisabled agents**: crea los agentes en modo deshabilitado.

    <!-- SCREENSHOT NEEDED: Paso OVH detailed del asistente con las seis opciones, incluida Autodisabled agents (la captura heredada disponible la omite). -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

Activar **Advanced statistics** y **Get monthly and overall costs** puede alargar la ejecución de la tarea, porque cada opción requiere peticiones adicionales a la API de OVHcloud.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total agents**: todos los agentes generados, incluido el agente global.
    - **VMs agents**: agentes de máquina virtual.
    - **Storage agents**: agentes de volumen.
    - **Server agents**: agentes de servidor dedicado.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    ![Resumen de una tarea de Discovery de OVH completada](../assets/images/discovery/ovh/ovh-task-summary.png)

2. **Los agentes.** El agente global más un agente por cada máquina virtual, volumen y servidor dedicado encontrado, según las opciones activadas.
3. **Los módulos.** El agente global tiene `OVH VMs count`; cada agente de máquina virtual tiene `<nombre VM>.status`. Véase [Comprender los resultados](#comprender-los-resultados).

## Comprender los resultados

### Agentes generados

| Agente | Alias | Dirección | Notas |
|--------|-------|-----------|-------|
| Agente global | `OVH` | Ninguna | Se crea en cada ejecución, salvo en enero con **Get monthly and overall costs** activado |
| Agente de máquina virtual | El nombre de la instancia | La dirección IPv4 de la instancia; vacía si no tiene | Uno por nombre de instancia de cada proyecto de Public Cloud: las instancias con el mismo nombre en proyectos distintos comparten agente. Solo se crea con **Monitor virtual machines** activado. La descripción incluye la región de la instancia |
| Agente de volumen | El nombre del volumen | Ninguna | Solo se crea con **Scan Volumes** activado |
| Agente de servidor dedicado | El nombre del servidor | La dirección IP del servidor | Solo se crea con **Scan Servers** activado |

Todos los agentes se crean en el grupo de la tarea. Con **Autodisabled agents** activado se crean en modo deshabilitado.

### Módulos por agente

**Agente global**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `OVH VMs count` | `generic_data` | Siempre | Instancias encontradas en todos los proyectos de Public Cloud, independientemente de **Monitor virtual machines** |
| `OVH total costs` | `generic_data` | **Get monthly and overall costs** | Suma de las facturas de la cuenta, con impuestos |
| `OVH month costs` | `generic_data` | **Get monthly and overall costs** | Suma, con impuestos, de las facturas fechadas desde el primer día del mes anterior hasta el momento de la ejecución |

**Agente de máquina virtual**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `<nombre VM>.status` | `generic_proc` | Siempre | `1` si el estado de la instancia es `ACTIVE`, `0` en otro caso |
| `<nombre VM>cpu:max`, `<nombre VM>cpu:used` | `generic_data` | **Advanced statistics** | Estadísticas de CPU informadas por OVHcloud |
| `<nombre VM>mem:max`, `<nombre VM>mem:used` | `generic_data` | **Advanced statistics** | Estadísticas de memoria informadas por OVHcloud |
| `<nombre VM>net:rx`, `<nombre VM>net:tx` | `generic_data` | **Advanced statistics** | Red recibida y enviada, según informa OVHcloud |

Los nombres de los módulos de estadísticas son el nombre de la instancia seguido directamente de la métrica, sin separador antes de `cpu`, `mem` o `net`. Cada valor es el último punto de datos que OVHcloud devuelve para la última semana.

**Agente de volumen**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<nombre volumen>.status` | `generic_data_string` | Estado del volumen |
| `<nombre volumen>.size` | `generic_data` | Tamaño del volumen |
| `<nombre volumen>.type` | `generic_data_string` | Tipo de volumen |
| `<nombre volumen>.bootable` | `generic_data_string` | Si el volumen es arrancable |
| `<nombre volumen>.region` | `generic_data_string` | Región del volumen |
| `<nombre volumen>.creationDate` | `generic_data_string` | Fecha de creación |
| `<nombre volumen>.attachedTo` | `generic_data_string` | Identificadores de las instancias a las que está asociado el volumen, separados por espacios |

**Agente de servidor dedicado**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<nombre servidor>.status` | `generic_proc` | `1` si el estado del servidor es `ok`, `0` en otro caso |
| `<nombre servidor>.powerState` | `generic_data_string` | Estado de energía |
| `<nombre servidor>.datacenter` | `generic_data_string` | Centro de datos |
| `<nombre servidor>.region` | `generic_data_string` | Región |
| `<nombre servidor>.linkSpeed` | `generic_data` | Velocidad del enlace |
| `<nombre servidor>.availabilityZone` | `generic_data_string` | Zona de disponibilidad |
| `<nombre servidor>.os` | `generic_data_string` | Sistema operativo |
| `<nombre servidor>.rack` | `generic_data_string` | Rack |
| `<nombre servidor>.reverse` | `generic_data_string` | DNS inverso |
| `<nombre servidor>.supportLevel` | `generic_data_string` | Nivel de soporte |
| `<nombre servidor>.commercialRange` | `generic_data_string` | Gama comercial |

### Cómo se identifican los agentes

Cada agente se identifica mediante un hash de su prefijo y su nombre; los agentes de volumen y de servidor dedicado incluyen además el identificador de OVHcloud del recurso. Los agentes con la misma identidad siguen informando al mismo agente de Pandora FMS entre ejecuciones, por lo que renombrar una máquina virtual en OVHcloud genera un agente nuevo.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta a un archivo de configuración descrito en [Archivo de configuración](#archivo-de-configuracion):

```bash
./pandora_ovh --conf <PATH_TO_CONFIG>
```

Imprime un resumen JSON y envía un archivo de datos por agente con el modo de transferencia configurado:

```json
{"summary": {"Total agents": 13, "VMs agents": 8, "Storage agents": 1, "Server agents": 3}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`. En modo `tentacle`, el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

El archivo de configuración contiene las credenciales de OVHcloud. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción de salida detallada ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`Error: Connector Cannot create client to OVH API`**: no se pudo crear el cliente de la API de OVHcloud con las credenciales proporcionadas.
- **`Error getting instances: Unexpected error`**: no se pudieron listar los proyectos de Public Cloud o sus instancias. Compruebe la conectividad, las tres credenciales y que la consumer key esté autorizada para `/cloud/project`.
- **`Error: Getting volumes`, `Error: Getting servers` o `Error: Getting costs`**: falló la petición correspondiente; el mensaje incluye el error devuelto por OVHcloud. Compruebe la ruta correspondiente en [Acceso a la API de OVHcloud](#acceso-a-la-api-de-ovhcloud).
- **`Error: Getting metrics ... for instance: <id>`**: no se pudieron obtener las estadísticas de esa instancia. Sus demás módulos se generan igualmente.
- **`Error while reading configuration file`**: no se puede leer el archivo de configuración indicado en `--conf` (ejecución manual).
- **No hay agentes de máquina virtual**: **Monitor virtual machines** está desactivado. El agente global sigue informando del número de instancias encontradas.
- **No hay módulos de estadísticas**: **Advanced statistics** está desactivado, o lo está **Monitor virtual machines**.
- **Menos agentes de los esperados**: solo se crean los tipos de recurso activados en la tarea, y solo se analizan los proyectos de Public Cloud, volúmenes y servidores dedicados visibles para las credenciales.

## Referencia

### Parámetros de la tarea

#### OVH base

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| OVH application key | `_applicationKey_` | password | — | Obligatorio. Application key de OVHcloud |
| OVH application secret | `_applicationSecret_` | password | — | Obligatorio. Application secret de OVHcloud |
| OVH consumer key | `_consumerKey_` | password | — | Obligatorio. Consumer key de OVHcloud |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de Tentacle |

#### OVH detailed

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| Scan Volumes | `_getStorage_` | checkbox | activado | Agentes de volumen |
| Scan Servers | `_getServers_` | checkbox | activado | Agentes de servidor dedicado |
| Get monthly and overall costs | `_getCost_` | checkbox | desactivado | Módulos de costes en el agente global |
| Monitor virtual machines | `_scanVms_` | checkbox | activado | Agentes de máquina virtual |
| Advanced statistics | `_advanceMonitoring_` | checkbox | desactivado | Se muestra con **Monitor virtual machines** activado. Módulos de rendimiento |
| Autodisabled agents | `_autodisabledAgents_` | checkbox | desactivado | Crea los agentes en modo deshabilitado |

### Archivo de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no sea numérico se lee como `0`.

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `application_key` | — | Obligatorio. Application key de OVHcloud |
| `application_secret` | — | Obligatorio. Application secret de OVHcloud |
| `consumer_key` | — | Obligatorio. Consumer key de OVHcloud |
| `agents_group_name` | `ovh` | Grupo de los agentes generados |
| `interval` | `300` | Intervalo de los agentes, en segundos |
| `prefix` | vacío | Prefijo añadido al alias de cada agente |
| `transfer_mode` | `local` | `local` o `tentacle` |
| `data_dir` | `/var/spool/pandora/data_in/` | Carpeta de los archivos de datos en modo `local` |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `scan_vms` | `0` | Agentes de máquina virtual |
| `storage` | `0` | Agentes de volumen |
| `servers` | `0` | Agentes de servidor dedicado |
| `cost` | `0` | Módulos de costes |
| `advance_monitoring` | `0` | Módulos de rendimiento de las máquinas virtuales |
| `autodisabled_agents` | `0` | Crear los agentes en modo deshabilitado |

A diferencia de la tarea de Discovery, donde **Scan Volumes**, **Scan Servers** y **Monitor virtual machines** vienen activados por defecto, en un archivo de configuración todas las opciones de recurso valen `0` salvo que las establezca.

Ejemplo:

```ini
application_key     = <APPLICATION_KEY>
application_secret  = <APPLICATION_SECRET>
consumer_key        = <CONSUMER_KEY>

agents_group_name   = OVH
interval            = 300
prefix              = ovh.
transfer_mode       = tentacle
tentacle_ip         = <TENTACLE_SERVER_IP>
tentacle_port       = 41121

scan_vms            = 1
storage             = 1
servers             = 1
cost                = 0
advance_monitoring  = 0
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | OVH |
| Identificador | `pandorafms.ovh` |
| Versión | `1.1` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.ovh](https://marketplace.pandorafms.com/entries/pandorafms.ovh), actualizada el 2026-09-09 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
