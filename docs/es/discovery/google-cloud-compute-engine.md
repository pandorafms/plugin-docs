# Google Cloud Compute Engine Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Google Cloud Compute Engine monitoriza instancias de máquina virtual de Google Cloud Compute Engine y las zonas que las contienen. Consulta las API de Compute Engine y Cloud Monitoring de un proyecto de Google Cloud y convierte el resultado en agentes y módulos de Pandora FMS: estado de la instancia y, opcionalmente, rendimiento de CPU, memoria, disco, IOPS y red.

Una tarea de Discovery genera tres tipos de agentes:

- **Un agente global de estadísticas** (opcional) con el número de instancias monitorizadas.
- **Un agente por cada zona monitorizada**, con módulos de resumen agregados sobre las instancias monitorizadas de esa zona.
- **Un agente por cada instancia monitorizada**, con su estado y sus módulos de rendimiento. El agente de la instancia es hijo del agente de su zona.

Una zona se puede seleccionar completa, y entonces se monitoriza cada instancia que contiene, incluidas las que se creen más adelante. También se pueden seleccionar instancias individuales sin seleccionar su zona.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.gcp.ce`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a las API de Google Cloud | `Requerido` | El addon llama a la API de Compute Engine (`compute`, `v1`) y a la API de Cloud Monitoring (`monitoring`, `v3`) |
| Clave de cuenta de servicio del proyecto de Google Cloud a monitorizar | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Prerrequisitos](#prerrequisitos) |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a las API de Google Cloud, de forma directa o a través de un proxy HTTP.
2. **Una clave de cuenta de servicio** (el fichero de clave JSON) del proyecto de Google Cloud que contiene las instancias, registrada en el almacén de credenciales de Pandora FMS como credencial de Google Cloud Platform. La clave debe incluir los campos `project_id` y `client_email`; el addon monitoriza el proyecto indicado en `project_id`.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye sus propios ejecutables, `bin/pandora_gcp_ce` y `bin/google_instances`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Permisos de Google Cloud

El addon realiza únicamente peticiones de lectura con la cuenta de servicio. Las que emite dependen de las opciones que active:

| Petición a la API | Uso |
|-------------------|-----|
| Compute Engine `instances.aggregatedList` | Listar zonas e instancias (siempre) |
| Cloud Monitoring `projects.timeSeries.list` | Valores de CPU, memoria, disco, IOPS y red (con **Scan and general monitoring** activado) |

Conceda a la cuenta de servicio roles o permisos que permitan estas dos peticiones sobre el proyecto. No se ha verificado ningún rol predefinido concreto para esta versión, así que elija el rol más restrictivo que las cubra en su organización.

Trate el fichero de clave como un secreto: quien lo posea puede actuar como la cuenta de servicio.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.gcp.ce](https://marketplace.pandorafms.com/entries/pandorafms.gcp.ce)

Cárguelo en Pandora FMS. Una vez cargado, **Google Cloud Compute Engine** está disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Google Cloud Compute Engine**. La consola presenta los campos en tres pasos; cada campo está documentado en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Task Setup** — credenciales, opciones de ejecución y de agentes:

    - **GCP Credentials**: la credencial de Google Cloud registrada en el almacén de credenciales.
    - **Max threads**: número de grupos en los que se dividen las zonas e instancias monitorizadas.
    - **Use proxy** y **Proxy url**: enrutan las peticiones a Google Cloud a través de un proxy.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: destino y forma de envío de los datos de los agentes generados. Rara vez hace falta cambiarlos.
    - **Add global stats agent** y **Stats agent name**: crean el agente global y permiten nombrarlo.

    <!-- SCREENSHOT NEEDED: Paso Task Setup del asistente con GCP Credentials, Max threads, proxy, Tentacle y agente de estadísticas, sin credenciales ni direcciones reales. -->

2. **Instance explorer** — un árbol de zonas e instancias leído de su proyecto de Google Cloud con la credencial seleccionada. Marque una zona para monitorizarla junto con todas sus instancias, o marque instancias individuales. Las instancias se agrupan por tipo de máquina dentro de cada zona.

    ![Paso Instance explorer con el árbol de zonas e instancias](../assets/images/discovery/google-cloud-compute-engine/gcp-ce-instance-explorer.png)

3. **Metrics** — los valores de rendimiento recopilados:

    - **Scan and general monitoring**: habilita las opciones siguientes.
    - **Cpu performance summary**, **IOPs performance summary**, **Disk performance summary**, **Network performance summary** y **Memory performance summary**: se muestran solo con **Scan and general monitoring** activado.

    <!-- SCREENSHOT NEEDED: Paso Metrics del asistente con Scan and general monitoring y las casillas de resumen de rendimiento. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total agents**: todos los agentes generados, incluido el agente global si está activado.
    - **Zones agents**: zonas monitorizadas.
    - **Instances agents**: instancias monitorizadas.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    ![Resumen de ejecución con Total agents, Zones agents e Instances agents](../assets/images/discovery/google-cloud-compute-engine/gcp-ce-task-summary.png)

2. **Los agentes.** Uno por cada zona seleccionada, uno por instancia y, si está activado, el agente global. Los agentes de instancia son hijos de su agente de zona.

3. **Los módulos.** Todo agente de instancia tiene `State` e `Instance State (bool)`. Los módulos de rendimiento aparecen solo en instancias en ejecución; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Padre | Notas |
|--------|-------|-------|-------|
| Agente global | El **Stats agent name**, o `Google Cloud Platform` si está vacío | Ninguno | Se crea solo con **Add global stats agent** activado |
| Agente de zona | El nombre de la zona, por ejemplo `europe-west1-b` | El agente global solo si se indicó un **Stats agent name** | Uno por zona seleccionada |
| Agente de instancia | El nombre de la instancia | Su agente de zona | Uno por instancia, creado una sola vez aunque se seleccionen la instancia y su zona. La versión del agente es el tipo de máquina y la dirección es la IP interna seguida de la dirección externa, si la tiene |

La identidad del agente no depende de la tarea. Los agentes de zona se identifican por la cuenta de servicio (`client_email`) y la zona, y los de instancia por la cuenta de servicio y el nombre de la instancia. El agente global se identifica por la cuenta de servicio cuando no tiene nombre, y por el **Stats agent name** en caso contrario. Mover una zona o instancia entre tareas que usan la misma cuenta de servicio sigue reportando al mismo agente y conserva su histórico.

Todos los agentes informan el nombre de sistema operativo `Google`, y `compute engine` como versión del sistema operativo en zonas e instancias.

### Módulos por agente

**Agente global**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `GCP CE Instances count` | `generic_data` | Instancias encontradas en las zonas e instancias seleccionadas |

**Agente de zona**

| Módulo | Condición | Descripción |
|--------|-----------|-------------|
| `summary.google.compute engine.instances` | Siempre | Instancias monitorizadas en la zona |
| `summary.google.compute engine.CPUUtilization` | **Scan and general monitoring** y **Cpu performance summary** | CPU de las instancias en ejecución dividida por el número de instancias de la zona |
| `summary.google.compute engine.Ram Used`, `summary.google.compute engine.SwapInBytes` | **Scan and general monitoring** y **Cpu performance summary** | Suma de las instancias en ejecución que informan estos valores |
| `summary.google.compute engine.DiskReadBytes`, `summary.google.compute engine.diskWriteBytes` | **Scan and general monitoring** y **Disk performance summary** | Suma de las instancias en ejecución, en `Bytes` |
| `summary.google.compute engine.diskAverageIOLatency` | **Scan and general monitoring** y **Disk performance summary** | Suma de la latencia media de E/S de las instancias en ejecución que la informan |
| `summary.google.compute engine.DiskReadOps`, `summary.google.compute engine.DiskWriteOps` | **Scan and general monitoring** y **IOPs performance summary** | Suma de las instancias en ejecución |
| `summary.google.compute engine.NetworkPacketsIn`, `summary.google.compute engine.NetworkPacketsOut` | **Scan and general monitoring** y **Network performance summary** | Suma de las instancias en ejecución, en `packets` |

**Agente de instancia**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `State` | `generic_data_string` | Siempre | Estado de la instancia informado por Google Cloud |
| `Instance State (bool)` | `generic_proc` | Siempre | `1` si el estado es `RUNNING`, `0` en caso contrario |
| `CPUUtilization` | `generic_data` | En ejecución, **Cpu performance summary** | Uso de CPU |
| `Memory % Used` | `generic_data` | En ejecución, **Memory performance summary**, valor disponible | Porcentaje de memoria usada, en `%` |
| `Ram Used`, `SwapInBytesCount` | `generic_data` | En ejecución, **Memory performance summary**, valor disponible | Memoria usada en la VM y memoria leída hacia el invitado desde su propio espacio de swap. Google Cloud los informa solo para VM de la familia e2 |
| `DiskReadBytes`, `DiskWriteBytes` | `generic_data` | En ejecución, **Disk performance summary** | Bytes de disco leídos y escritos, en `Bytes` |
| `DiskAverageIOLatency` | `generic_data` | En ejecución, **Disk performance summary**, valor disponible | Latencia media de E/S de disco |
| `Disk % Used` | `generic_data` | En ejecución, **Disk performance summary**, valor disponible | Porcentaje de disco usado, en `%` |
| `DiskReadOps`, `DiskWriteOps` | `generic_data` | En ejecución, **IOPs performance summary** | Operaciones de lectura y escritura de disco |
| `NetworkPacketsIn`, `NetworkPacketsOut` | `generic_data` | En ejecución, **Network performance summary** | Paquetes de red recibidos y enviados, en `packets` |
| `NetworkBytesIn`, `NetworkBytesOut` | `generic_data` | En ejecución, **Network performance summary** | Bytes de red recibidos y enviados, en `bytes` |
| `TCPConnections` | `generic_data` | En ejecución, **Network performance summary**, valor disponible | Conexiones TCP |

«Valor disponible» significa que Cloud Monitoring devolvió un punto de datos para la métrica. En caso contrario el módulo no se crea.

### Cómo se obtienen los valores

- Los valores de rendimiento se leen de Cloud Monitoring en una ventana tan larga como el intervalo de la tarea, con un mínimo de 300 segundos, y se usa el primer punto de datos devuelto.
- Los módulos de rendimiento se crean solo para instancias en estado `RUNNING`.
- `Memory % Used`, `Disk % Used` y `TCPConnections` proceden de métricas publicadas bajo `agent.googleapis.com`; el resto de valores de rendimiento proceden de `compute.googleapis.com/instance/`.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable admite un único parámetro, la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_gcp_ce --conf <PATH_TO_CONFIG>
```

Imprime un resumen JSON y envía un fichero de datos por agente con el modo de transferencia configurado:

```json
{"summary": {"Total agents": 35, "Zones agents": 5, "Instances agents": 29}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`.

En modo de transferencia `local` los ficheros de datos se mueven a `data_dir`. En cualquier otro modo se envían con Tentacle, y el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

Un fichero de configuración contiene la clave de la cuenta de servicio codificada en `creds_b64`. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **El árbol de instancias está vacío**: el paso **Instance explorer** imprime `Error while parsing credentials: <error>` cuando la credencial no es JSON válido codificado en base64 o carece de `project_id`. En otro caso, compruebe la conectividad, el proxy y los permisos de la cuenta de servicio para la API de Compute Engine.
- **`Error while parsing configuration zones or instances`**: en un fichero de configuración, `gcp_zones` o `gcp_instances` no es un array JSON válido.
- **`Cannot create client to Google Compute API` o `Cannot create client to Google Monitoring API`**: el addon no pudo crear el cliente de la API. Compruebe la conectividad y la configuración del proxy.
- **Menos agentes de los esperados**: solo se monitorizan las zonas e instancias marcadas.
- **Una instancia no tiene módulos de rendimiento**: la instancia no está en `RUNNING`, **Scan and general monitoring** está desactivado, o la opción correspondiente está desactivada.
- **`Error while runing single thread`**: el procesamiento de un grupo de objetivos se detuvo con el error que sigue. Puede ocurrir cuando Cloud Monitoring no devuelve ningún punto de datos para una métrica de rendimiento de una instancia. Los objetivos restantes de ese grupo no producen agentes en esa ejecución.
- **Faltan los módulos de memoria, `Disk % Used` o `TCPConnections`**: Cloud Monitoring no devolvió ningún punto de datos para esas métricas, que solo están disponibles cuando la VM las publica.
- **Errores al llegar a Google Cloud a través de un proxy**: revise **Proxy url**. Si no incluye esquema, se le añade `http://`.
- **`Tentacle error:`**: no se pudo enviar el fichero de datos. El mensaje incluye el error devuelto por el cliente de Tentacle.

## Referencia

### Parámetros de la tarea

#### Task Setup

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| GCP Credentials | `_credentials_` | selector de credencial (Google Cloud Platform) | — | Obligatorio. Credencial registrada en el almacén de credenciales |
| Max threads | `_threads_` | número | `1` | Opcional. Las zonas e instancias se reparten en grupos, nunca más grupos que objetivos |
| Use proxy | `_useProxy_` | casilla | desactivada | Enruta las peticiones a Google Cloud a través de un proxy |
| Proxy url | `_proxyUrl_` | cadena | — | Opcional. Se muestra con **Use proxy** activado |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | — | Opcional. Opciones adicionales del cliente de Tentacle |
| Add global stats agent | `_statsAgent_` | casilla | activada | Crea el agente global |
| Stats agent name | `_statsAgentName_` | cadena | alias `Google Cloud Platform` | Opcional. Se muestra con **Add global stats agent** activado |

#### Instance explorer

| Campo | Macro | Tipo | Notas |
|-------|-------|------|-------|
| Google Cloud Compute Engine zones and instances | `_googleCEZones_`, `_googleCEInstance_` | árbol | Las zonas rellenan la lista de zonas y las instancias la de instancias. Opcional |

#### Metrics

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| Scan and general monitoring | `_googleCEInstanceSummary_` | casilla | desactivada | Habilita los módulos de rendimiento |
| Cpu performance summary | `_googleCECpuPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| IOPs performance summary | `_googleCEIopsPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Disk performance summary | `_googleCEDiskPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Network performance summary | `_googleCENetworkPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Memory performance summary | `_googleCEMemPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Los valores de lista son arrays JSON. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no sea un número se lee como `0`. Las claves desconocidas se ignoran.

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `agents_group_name` | `google` | Grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `threads` | `1` | Número de grupos en los que se reparten los objetivos |
| `transfer_mode` | `local` | `local` mueve los ficheros de datos a `data_dir`; cualquier otro valor los envía con Tentacle, lo que requiere `tentacle_ip` |
| `tentacle_client` | `tentacle_client` | Ejecutable del cliente de Tentacle |
| `tentacle_ip` | vacío | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `tentacle_opts` | vacío | Opciones adicionales del cliente de Tentacle |
| `data_dir` | `/var/spool/pandora/data_in/` | Destino de los ficheros de datos en modo `local` |
| `temporal` | `/tmp` | Directorio donde se escriben los ficheros de datos antes de enviarlos |
| `advance_monitoring` | `1` | Módulos de rendimiento; necesario para las cinco opciones siguientes |
| `cpu_summary` | `1` | Módulos de CPU |
| `mem_summary` | `1` | Módulos de memoria |
| `iops_summary` | `1` | Módulos de IOPS |
| `disk_summary` | `1` | Módulos de disco |
| `network_summary` | `1` | Módulos de red |
| `stats_agent` | `1` | Agente global |
| `stats_agent_name` | vacío | Nombre del agente global; alias `Google Cloud Platform` si está vacío |
| `gcp_zones` | `[]` | Zonas a monitorizar. Se monitoriza cada instancia encontrada en una zona listada |
| `gcp_instances` | `[]` | Nombres de las instancias a monitorizar |
| `use_proxy` | `0` | Usar un proxy |
| `proxy_url` | vacío | URL del proxy |
| `creds_b64` | vacío | Obligatorio. Base64 del fichero de clave JSON de la cuenta de servicio |

Ejemplo:

```ini
agents_group_name  = google
interval           = 300
threads            = 4
transfer_mode      = tentacle
tentacle_ip        = <TENTACLE_SERVER_IP>
tentacle_port      = 41121

advance_monitoring = 1
cpu_summary        = 1
mem_summary        = 1
iops_summary       = 1
disk_summary       = 1
network_summary    = 1

stats_agent        = 1
stats_agent_name   = GoogleCloud

gcp_zones          = ["<ZONE_NAME>"]
gcp_instances      = ["<INSTANCE_NAME>"]

creds_b64          = <BASE64_SERVICE_ACCOUNT_KEY>
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Google Cloud Compute Engine |
| Identificador | `pandorafms.gcp.ce` |
| Versión | `1.1` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.gcp.ce](https://marketplace.pandorafms.com/entries/pandorafms.gcp.ce), actualizada el 2025-06-01 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
