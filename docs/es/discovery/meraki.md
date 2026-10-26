# Meraki Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon Meraki Discovery monitoriza dispositivos de red Cisco Meraki a través de la API REST de Meraki Dashboard. Para una red Meraki lee el estado de los dispositivos de tres tipos de producto, **appliance**, **switch** y **wireless**, y convierte el resultado en agentes y módulos de Pandora FMS: estado del dispositivo, estado de los uplinks y puntuación de rendimiento de los appliances, estado y tráfico de los puertos de los switches, caudal y clientes conectados de los dispositivos wireless y, opcionalmente, el tráfico agregado de los appliances de la red.

Una tarea de Discovery genera estos agentes:

- **Un agente por appliance**, con su estado y el estado de sus uplinks.
- **Un agente por switch**, con su estado y el estado y tráfico de cada puerto.
- **Un agente por dispositivo wireless**, con su estado, caudal y número de clientes.
- **Un agente de tráfico de red** (opcional), con el tráfico agregado de los appliances de la red.

La tarea se autentica con un token Bearer y envía los datos de los agentes generados a Pandora FMS mediante Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.meraki`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a la API de Meraki Dashboard | `Required` | Todas las peticiones van a la URL de la API configurada en la tarea |
| Token Bearer de la API de Meraki con acceso a la organización | `Required` | Prerrequisito, no una declaración de compatibilidad |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Not validated` | No se ha registrado una matriz de versiones para este addon |
| Modelos y firmware concretos de Meraki | `Not validated` | No se ha registrado una matriz de modelos ni de firmware |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery hasta la API de Meraki Dashboard (el formulario de la tarea sugiere `https://api.meraki.com/api/v1` como URL).
2. **Un token Bearer de la API de Meraki** que pueda leer la organización, sus redes y sus dispositivos. El addon solo realiza peticiones de lectura (`GET`).
3. **El ID de la organización** y, de la red a monitorizar, su **nombre** (o parte de él) y su **ID de red**. Consulte [Configurar la tarea de Discovery](#configurar-la-tarea-de-discovery) para saber cómo se usa cada valor.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla. Los datos generados se envían con Tentacle, por lo que la dirección y el puerto del servidor Tentacle deben ser accesibles desde el servidor de Discovery.

El addon incluye su propio ejecutable, `bin/pandora_meraki`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.meraki](https://marketplace.pandorafms.com/entries/pandorafms.meraki)

Cárguelo en Pandora FMS. Una vez cargado, **Meraki** está disponible entre las aplicaciones al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Application → Meraki**. La consola presenta los campos en dos pasos, **Meraki base** y **Meraki Detailed**; todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

Una tarea monitoriza **una red**. Para monitorizar varias redes, cree una tarea por red.

1. **Meraki base** — conexión y objetivo:

    - **ID**: texto que identifica la red por su nombre. El addon busca la primera red de la organización cuyo **nombre** contenga este texto (coincidencia de subcadena, no una expresión regular) y monitoriza los dispositivos que pertenecen a ella.
    - **Token**: el token Bearer de la API de Meraki.
    - **Url**: la URL base de la API, por ejemplo `https://api.meraki.com/api/v1`.
    - **Organization**: el ID de la organización.
    - **Network**: el **ID** de la red. Se usa tal cual en las peticiones a nivel de red (tráfico agregado de appliances y uso wireless), por lo que debe introducir el ID de la misma red seleccionada con **ID**.
    - **Use location** y **Location**: grupos secundarios añadidos a los agentes generados.
    - **Tentacle IP** y **Tentacle port**: destino de los datos de los agentes generados.

    <!-- SCREENSHOT NEEDED: Paso Meraki base del asistente con ID, Token, Url, Organization, Network, Use location y los campos de Tentacle, sin token, organización ni direcciones reales. -->

2. **Meraki Detailed** — nombres y alcance:

    - **Use prefix**, **Agent Prefix** y **Module Prefix**: prefijos añadidos a los nombres de agentes y módulos.
    - **Interval monitoring**: ventana de tiempo de las estadísticas de puertos de los switches, en segundos.
    - **Use API** y los campos **Api**: campos reservados que esta versión no utiliza. Consulte [Parámetros de la tarea](#parametros-de-la-tarea).
    - **Name Agent Hostname**: nombra los agentes con el nombre del dispositivo en lugar de su número de serie.
    - **Scan appliances**, **Scan switches**, **Scan wireless** y **Scan Appliance Traffic Network**: tipos de dispositivo y datos a recoger.

    <!-- SCREENSHOT NEEDED: Paso Meraki Detailed del asistente con los prefijos, Interval monitoring, Name Agent Hostname y las casillas de escaneo. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de tareas y se aplican a los agentes que crea la tarea.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total agents**: todos los agentes generados.
    - **Total appliance agents**, **Total switches agents** y **Total wireless agents**: agentes por tipo de dispositivo.
    - **Total network appliance traffic agents**: `1` cuando se generó el agente de tráfico de red.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea Meraki en Discovery con los contadores totales de agentes. -->

2. **Los agentes.** Sus alias empiezan por el prefijo de agente (si existe), seguido de `Appliance_`, `Switch_` o `Wireless_` y el nombre o número de serie del dispositivo.

3. **Los módulos.** Todos los agentes de dispositivo tienen un módulo `status`. Consulte [Interpretar los resultados](#interpretar-los-resultados) para el resto.

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Dirección | Grupos secundarios |
|--------|-------|-----------|--------------------|
| Appliance | `<prefijo de agente>Appliance_<nombre o serie>` | Dirección IP pública del dispositivo | **Location**, más `Router` |
| Switch | `<prefijo de agente>Switch_<nombre o serie>` | Dirección IP pública del dispositivo | **Location**, más `Switch` |
| Wireless | `<prefijo de agente>Wireless_<nombre o serie>` | Dirección IP pública del dispositivo | **Location**, más `Access Points` |
| Tráfico de red | `<prefijo de agente> Traffic Appliance_<Network>` | Ninguna | **Location** |

- Con **Name Agent Hostname** activado, los agentes switch y wireless usan el nombre del dispositivo, recurriendo al número de serie cuando el dispositivo no tiene nombre; desactivado, se usa el número de serie. Los agentes appliance también leen el ajuste, pero toman el nombre de los datos de switch, que la ruta de appliance no tiene: con **Name Agent Hostname** activado la ejecución termina con un error al llegar a un appliance. Desactívelo para crear agentes appliance con el número de serie.
- La identidad del agente se deriva del prefijo de agente y del nombre o serie utilizado. Cambiar el prefijo o el ajuste **Name Agent Hostname**, o renombrar un dispositivo, produce un agente nuevo en lugar de actualizar el anterior.
- Solo producen agentes los dispositivos que pertenecen a la red monitorizada y cuyo tipo está habilitado (**Scan appliances**, **Scan switches**, **Scan wireless**).
- Los agentes informan con el grupo y el intervalo de la tarea.

### Módulos por agente

Los nombres de módulo se muestran sin el prefijo de módulo.

**Agente appliance**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `status` | `generic_proc` | Siempre | `1` cuando el estado del dispositivo es `online`, `0` en otro caso. La descripción contiene el estado que informa Meraki |
| `perfScore` | `generic_data` | Cuando Meraki devuelve una puntuación de rendimiento del dispositivo | Puntuación de rendimiento, en `%` |
| `Uplink <interface>_ifOperStatus` | `generic_proc` | Uno por cada uplink informado para el dispositivo | `1` cuando el estado del uplink es `active`, `0` en otro caso. La descripción contiene el estado del uplink |

**Agente switch**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `status` | `generic_proc` | Siempre | `1` cuando el estado del dispositivo es `online`, `0` en otro caso |
| `Port <portId>_ifOperStatus` | `generic_proc` | Uno por puerto | `1` cuando el estado del puerto es `Connected`, `0` en otro caso |
| `Port <portId>_ifOutOctets` | `generic_data` | Uno por puerto | Tráfico enviado por el puerto, en `Kbps` |
| `Port <portId>_ifInOctets` | `generic_data` | Uno por puerto | Tráfico recibido por el puerto, en `Kbps` |

**Agente wireless**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `status` | `generic_proc` | Siempre | `1` cuando el estado del dispositivo es `online`, `0` en otro caso |
| `totalKbps` | `generic_data` | Cuando Meraki devuelve datos de uso | Caudal total, en `Kbps` |
| `sentKbps` | `generic_data` | Cuando Meraki devuelve datos de uso | Caudal enviado, en `Kbps` |
| `receivedKbps` | `generic_data` | Cuando Meraki devuelve datos de uso | Caudal recibido, en `Kbps` |
| `clientCount` | `generic_data` | Cuando Meraki devuelve el número de clientes | Clientes conectados |

**Agente de tráfico de red** (cuando **Scan Appliance Traffic Network** está activado)

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `Traffic appliance <Network> total_sent` | `generic_data` | Suma de los datos enviados de todas las aplicaciones que Meraki informa para los appliances de la red |
| `Traffic appliance <Network> total_recv` | `generic_data` | Suma de los datos recibidos de las mismas aplicaciones |
| `Traffic appliance <Network> total_clients` | `generic_data` | Suma del número de clientes de las mismas aplicaciones |

### Cómo se obtienen los valores

- El estado de los dispositivos, el estado de los uplinks de los appliances y la lista de dispositivos se leen para toda la organización y después se filtran por la red monitorizada.
- Las estadísticas de puertos de los switches abarcan los últimos **Interval monitoring** segundos.
- El caudal wireless, el número de clientes y el tráfico de appliances de la red se leen para las últimas 86400 segundos (24 horas) y no son configurables.
- En los dispositivos wireless, los valores de los módulos son el primer punto de datos que Meraki devuelve para el dispositivo.
- El agente de tráfico de red se genera siempre que **Scan Appliance Traffic Network** está activado, incluso con **Scan appliances** desactivado.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable admite un único parámetro, la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_meraki --conf <PATH_TO_CONFIG>
```

Imprime un resultado de ejecución JSON con el resumen y los mensajes de error, y envía un fichero de datos por agente con el modo de transferencia configurado. En modo `tentacle` (el predeterminado), el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

El fichero de configuración contiene el token Bearer. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es la información del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`error: id its required`, `error: base url its required`, `error: bearer token its required`, `error: organization its required`, `error: network its required`**: el ajuste indicado está vacío. Los cinco son obligatorios.
- **`Meraki nets could not be obtained.`**: la petición para listar las redes de la organización no devolvió datos. Compruebe la **Url**, el ID de **Organization**, la validez del **Token** y la conectividad con la API.
- **`Request Error: <detalle>`**: falló la conexión con la API. El detalle contiene el error del cliente HTTP.
- **`Error: 204 : Data could not be obtained.` y `Error: 204 : PerfScore data could not be obtained.`**: Meraki respondió sin contenido a una petición. Los módulos correspondientes no se crean.
- **No se genera ningún agente**: el texto de **ID** no coincide con el nombre de ninguna red de la organización, la red monitorizada no tiene dispositivos de los tipos habilitados, o los tipos de dispositivo están desactivados.
- **Sin módulos `perfScore` o `Uplink` en un appliance**: Meraki no devolvió datos de rendimiento o de uplinks para ese dispositivo.
- **Sin módulos wireless además de `status`**: las peticiones wireless a nivel de red no devolvieron datos para el dispositivo en las últimas 24 horas.
- **`Error getting switch data: <detalle>`, `Error getting wireless data: <detalle>` o `Error getting appliance data: <detalle>`**: no se pudieron procesar los datos de un dispositivo. El detalle contiene la causa.
- **Los datos no llegan a Pandora FMS**: compruebe **Tentacle IP** y **Tentacle port**, y la conectividad con el servidor Tentacle.

## Referencia

### Parámetros de la tarea

#### Meraki base

| Campo | Macro | Tipo | Obligatorio | Valor por defecto | Notas |
|-------|-------|------|-------------|-------------------|-------|
| ID | `_id_` | cadena | Sí | — | Texto contenido en el nombre de la red a monitorizar. Se usa la primera red que coincide |
| Token | `_token_` | contraseña | Sí | — | Token Bearer de la API de Meraki |
| Url | `_baseUrl_` | cadena | Sí | — | URL base de la API. El formulario sugiere `https://api.meraki.com/api/v1` |
| Organization | `_organization_` | cadena | Sí | — | ID de la organización |
| Network | `_network_` | cadena | Sí | — | ID de red usado en las peticiones a nivel de red |
| Use location | `_useLocation_` | casilla | No | desactivada | Habilita **Location** |
| Location | `_location_` | cadena | No | — | Grupos secundarios añadidos a los agentes. Se muestra con **Use location** activado |
| Tentacle IP | `_tentacleIP_` | cadena | No | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | No | `41121` | Puerto de Tentacle |

#### Meraki Detailed

| Campo | Macro | Tipo | Obligatorio | Valor por defecto | Notas |
|-------|-------|------|-------------|-------------------|-------|
| Use prefix | `_usePrefix_` | casilla | No | desactivada | Habilita los campos de prefijo |
| Agent Prefix | `_agentPrefix_` | cadena | No | — | Se añade a los nombres y alias de los agentes. Se muestra con **Use prefix** activado |
| Module Prefix | `_modulePrefix_` | cadena | No | — | Se añade a los nombres de los módulos. Se muestra con **Use prefix** activado |
| Interval monitoring | `_intervalMonitoring_` | número | No | `3600` | Ventana de tiempo de las estadísticas de puertos de los switches, en segundos |
| Use API | `_useApi_` | casilla | No | desactivada | Habilita los campos **Api**. Esta versión no los utiliza |
| Api url | `_apiUrl_` | cadena | No | — | No lo utiliza esta versión. Se muestra con **Use API** activado |
| Api user | `_apiUser_` | cadena | No | — | No lo utiliza esta versión |
| Api password | `_apiPass_` | contraseña | No | — | No lo utiliza esta versión |
| Api user password | `_apiUserpass_` | contraseña | No | — | No lo utiliza esta versión |
| Name Agent Hostname | `_agentHostname_` | casilla | No | activada | Activada: agentes con el nombre del dispositivo. Desactivada: con el número de serie |
| Scan appliances | `_scanAppliance_` | casilla | No | activada | Genera agentes appliance |
| Scan switches | `_scanSwitch_` | casilla | No | activada | Genera agentes switch |
| Scan wireless | `_scanWireless_` | casilla | No | activada | Genera agentes wireless |
| Scan Appliance Traffic Network | `_scanApplianceTrafficNetwork_` | casilla | No | activada | Genera el agente de tráfico de red |

Esta versión no ofrece ninguna opción para monitorizar dispositivos cellular gateway de Meraki.

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea, sin secciones. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no es un número se lee como `0`.

| Clave | Obligatoria | Valor por defecto | Descripción |
|-------|-------------|-------------------|-------------|
| `id` | Sí | — | Texto contenido en el nombre de la red a monitorizar |
| `base_url` | Sí | — | URL base de la API |
| `bearer_token` | Sí | — | Token Bearer |
| `organization` | Sí | — | ID de la organización |
| `network` | Sí | — | ID de red usado en las peticiones a nivel de red |
| `location` | No | vacío | Grupos secundarios de los agentes |
| `agents_group_name` | No | vacío | Grupo de los agentes generados |
| `interval` | No | `300` | Intervalo de los agentes, en segundos |
| `agent_prefix` | No | vacío | Prefijo de los agentes |
| `module_prefix` | No | vacío | Prefijo de los módulos |
| `interval_monitoring` | No | `3600` | Ventana de tiempo de las estadísticas de puertos de los switches, en segundos |
| `agentname_hostname` | No | `1` | `1` nombra los agentes con el nombre del dispositivo, `0` con el número de serie |
| `scan_appliance` | No | `1` | Agentes appliance |
| `scan_switch` | No | `1` | Agentes switch |
| `scan_wireless` | No | `1` | Agentes wireless |
| `scan_traffic_appliance_network` | No | `1` | Agente de tráfico de red |
| `transfer_mode` | No | `tentacle` | `tentacle` envía los ficheros de datos con Tentacle; `local` los mueve al directorio de datos predeterminado de Pandora FMS (`/var/spool/pandora/data_in/`) |
| `tentacle_address` | No | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | No | `41121` | Puerto del servidor Tentacle |
| `tentacle_client` | No | `tentacle_client` | Ejecutable del cliente Tentacle |
| `tentacle_opts` | No | vacío | Opciones adicionales del cliente Tentacle. Esta versión lee el valor pero no lo pasa a la transferencia, que siempre se ejecuta sin opciones adicionales |
| `temporal` | No | `/tmp` | Directorio donde se escriben los ficheros de datos antes de enviarlos. Esta versión lee el valor pero no lo pasa a la transferencia, que siempre usa `/tmp` |
| `data_dir` | No | `/var/spool/pandora/data_in/` | Destino de los ficheros de datos en modo `local`. Esta versión lee el valor pero no lo pasa a la transferencia, que siempre usa `/var/spool/pandora/data_in/` |

Las claves `api_url`, `api_user`, `api_pass` y `api_user_pass` se aceptan pero esta versión no las utiliza.

Ejemplo:

```ini
base_url = https://api.meraki.com/api/v1
bearer_token = <API_TOKEN>
organization = <ORGANIZATION_ID>
id = <NETWORK_NAME_TEXT>
network = <NETWORK_ID>
location = <SECONDARY_GROUP>

agents_group_name = MerakiAgents
agent_prefix = Meraki
module_prefix = Meraki_
interval = 300
interval_monitoring = 3600
agentname_hostname = 1

scan_appliance = 1
scan_switch = 1
scan_wireless = 1
scan_traffic_appliance_network = 1

tentacle_address = <TENTACLE_SERVER_IP>
tentacle_port = 41121
```

### Peticiones a la API de Meraki

Todas las peticiones son `GET` con el token Bearer, enviadas a la **Url** configurada.

| Dato | Petición |
|------|----------|
| Redes de la organización | `/organizations/<organization>/networks` |
| Estado de los dispositivos | `/organizations/<organization>/devices/statuses` |
| Estado de los uplinks de los appliances | `/organizations/<organization>/uplinks/statuses` |
| Rendimiento del appliance | `/devices/<serial>/appliance/performance` |
| Tráfico de appliances de la red | `/networks/<network>/traffic` |
| Estado y tráfico de los puertos del switch | `/devices/<serial>/switch/ports/statuses` |
| Uso wireless | `/networks/<network>/wireless/usageHistory` |
| Clientes wireless | `/networks/<network>/wireless/clientCountHistory` |

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Meraki |
| Identificador | `pandorafms.meraki` |
| Versión | `1.1` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.meraki](https://marketplace.pandorafms.com/entries/pandorafms.meraki), actualizada el 2025-08-20 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
