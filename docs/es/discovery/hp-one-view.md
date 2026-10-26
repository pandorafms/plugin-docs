# HP One View Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon HP One View Discovery monitoriza el hardware de servidores y la appliance gestionados por un entorno HP OneView. Se conecta a la appliance de OneView con un usuario y una contraseña y convierte el resultado en agentes y módulos de Pandora FMS. De forma opcional, convierte las alertas activas de OneView en eventos de Pandora FMS.

Una tarea de Discovery puede generar:

- **Un agente por servidor** (opcional), con su estado de salud, su estado y su estado de alimentación, además de las últimas métricas de utilización que OneView informa para él.
- **Un agente de appliance** (opcional) con la capacidad, la disponibilidad y el porcentaje de uso de cada recurso que informa el estado de salud de la appliance.
- **Eventos** (opcional) para las alertas activas o bloqueadas de OneView, creados en el agente de appliance.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.hp.oneview`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a la appliance HP OneView | `Required` | El addon se conecta a la appliance con las credenciales de la tarea |
| Usuario de HP OneView con acceso de lectura al hardware de servidores y a la salud de la appliance | `Required` | Prerrequisito. Los roles necesarios no están documentados para este addon |
| Versiones concretas de HP OneView | `Not validated` | No se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Not validated` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery hasta la appliance HP OneView.
2. **Un usuario y una contraseña de HP OneView** que puedan leer los servidores y la salud de la appliance.
3. **Solo para crear eventos a partir de alertas**, todo lo siguiente:
    - Un token de la API v2 de Pandora FMS y la URL de la consola de Pandora FMS.
    - El ID numérico del grupo de Pandora FMS en el que se crean los eventos.
    - Acceso de lectura, desde el servidor de Discovery, al fichero de configuración del servidor de Pandora FMS (por defecto `/etc/pandora/pandora_server.conf`) y acceso de red a la base de datos de Pandora FMS definida en él. El addon lee los datos de conexión a la base de datos de ese fichero para localizar el ID del agente de appliance.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye su propio ejecutable, `bin/pandora_hponeview`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.hp.oneview](https://marketplace.pandorafms.com/entries/pandorafms.hp.oneview)

Cárguelo en Pandora FMS. Una vez cargado, **HP One View** estará disponible al crear tareas de Discovery, en la sección de aplicaciones (`app`).

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones de Discovery y elija **HP One View**. La consola presenta los campos en dos pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **HP one view base** — conexión y entrega:

    - **IP**: dirección de la appliance HP OneView.
    - **User** y **Password**: credenciales del usuario de OneView.
    - **Tentacle IP** y **Tentacle port**: destino de los datos de los agentes generados. Por defecto `127.0.0.1` y `41121`.

    ![Paso HP one view base del asistente con los campos IP, User, Password, Tentacle IP y Tentacle port](../assets/images/discovery/hp-one-view/hp-one-view-wizard-base-step.png)

2. **HP one view Detailed** — qué recopilar:

    - **Use prefix** y **Prefix**: anteponen un texto a los alias de los agentes y a los nombres de los módulos.
    - **Scan appliances** y **Scan servers**: crean el agente de appliance y los agentes de servidor. Ambos están activados por defecto.
    - **Scan alerts**: crea eventos a partir de las alertas de OneView. Activado por defecto. Muestra **API Url**, **API Token**, **Server conf** y **Events ID group**.

    <!-- SCREENSHOT NEEDED: HP one view Detailed wizard step showing the prefix, scan checkboxes and the alert fields, with no real tokens or addresses. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

Las alertas están activadas por defecto, pero necesitan **API Url**, **API Token** y **Events ID group** para funcionar. Si no necesita eventos, desactive **Scan alerts**; de lo contrario la tarea informa de un error en cada ejecución.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que termina correctamente informa de:

    - **Total agents**: todos los agentes generados, servidores y appliance.
    - **Total server agents**: agentes de servidor generados.
    - **Total alerts**: eventos creados a partir de alertas.

    Los errores se registran en la información de ejecución de la tarea.

    ![Resumen de ejecución de una tarea HP One View con Total agents, Total alerts y Total server agents](../assets/images/discovery/hp-one-view/hp-one-view-task-execution-summary.png)

2. **Los agentes.** Uno por servidor cuando **Scan servers** está activado, y el agente de appliance cuando **Scan appliances** está activado.
3. **Los módulos.** Cada agente de servidor tiene `status`, `state` y `powerState`; consulte [Interpretar los resultados](#interpretar-los-resultados).
4. **Los eventos**, cuando **Scan alerts** está activado. El agente de appliance debe existir ya, por lo que en la primerísima ejecución el paso de alertas se omite con un error que pide volver a ejecutar la tarea. Ejecútela una segunda vez para crear los eventos.

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Sistema operativo | Notas |
|--------|-------|-------------------|-------|
| Agente de servidor | `<prefix><nombre del servidor>` | Sistema operativo y modelo informados por OneView, como `<operatingSystem> <model>` | Uno por servidor del entorno OneView |
| Agente de appliance | `<prefix> Appliances` | No definido | Uno por instalación de Pandora FMS, consulte la nota siguiente |

La identidad del agente de servidor se deriva del prefijo y del nombre del servidor. La identidad del agente de appliance es siempre la misma, sea cual sea el prefijo o el entorno OneView: dos tareas, incluso contra appliances distintas, informan al mismo agente de appliance.

### Módulos por agente

**Agente de servidor**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<prefix>status` | `generic_proc` | `1` cuando el estado del servidor en OneView es `OK`, `0` en otro caso |
| `<prefix>state` | `generic_data_string` | Estado del servidor informado por OneView |
| `<prefix>powerState` | `generic_data_string` | Estado de alimentación informado por OneView |
| `<prefix><nombre de la métrica>` | `generic_data` | Un módulo por cada métrica de utilización que OneView devuelve para el servidor, con su última muestra. Las métricas disponibles dependen del servidor |

**Agente de appliance**

Para cada recurso del estado de salud de la appliance, donde `<resource_id>` y `<resource_type>` son los que informa OneView:

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<prefix><resource_id> <resource_type> available` | `generic_data_string` | Cantidad disponible, tal como la informa OneView |
| `<prefix><resource_id> <resource_type> capacity` | `generic_data_string` | Capacidad, tal como la informa OneView |
| `<prefix><resource_id> <resource_type> used_percent` | `generic_data` | Porcentaje de uso en `%`, calculado como `100 - (available × 100 / capacity)` y redondeado a dos decimales. Es `0` cuando la capacidad es `0` |

El porcentaje de uso se calcula solo con la parte numérica de los valores. El texto de la unidad se ignora.

### Eventos a partir de alertas

Cuando **Scan alerts** está activado, el addon lee las primeras 10 alertas que devuelve OneView. Por cada una cuyo estado sea `Active` o `Locked`, crea un evento de Pandora FMS cuyo texto es la descripción de la alerta, asignado al agente de appliance y al grupo indicado en **Events ID group**. La severidad del evento es `critical` para una alerta Critical y `warning` para una alerta Warning. El addon no comprueba si el evento ya existe, por lo que la misma alerta genera un evento nuevo en cada ejecución mientras siga activa.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta de un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_hponeview --conf <PATH_TO_CONFIG>
```

Imprime un resumen JSON y envía un fichero de datos por agente con el modo de transferencia configurado:

```json
{"summary": {"Total agents": 3, "Total server agents": 2, "Total alerts": 0}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes.

El fichero de configuración contiene en texto claro la contraseña de OneView y el token de la API. Protéjalo con permisos restrictivos.

### Limitaciones

- En cada ejecución solo se evalúan las primeras 10 alertas que devuelve OneView.
- Un servidor cuyos datos no se pueden leer se omite sin mensaje de error.
- El campo **Max threads** se muestra en la consola, pero esta versión del addon no lo utiliza.
- Si existe un fichero `config.json` junto al ejecutable, su contenido sustituye a los datos de conexión a OneView de la tarea.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`Error connecting: ...`**: falló la conexión con la appliance de OneView. Compruebe **IP**, **User**, **Password** y el acceso de red.
- **`Error alerts: if it is the first execution of the plugin, try again, it will be generated in the second execution`**: el agente de appliance aún no existe en Pandora FMS. Vuelva a ejecutar la tarea.
- **`Error alerts: missing same parameter check events_id_group,api_url and token_api`**: **Scan alerts** está activado pero **Events ID group**, **API Url** o **API Token** está vacío.
- **`error getting id_agent appliance: ...`**: el addon no pudo leer el fichero de configuración del servidor de Pandora FMS o conectarse a la base de datos que define. Compruebe **Server conf** y el acceso a la base de datos desde el servidor de Discovery.
- **No se crean eventos pero no se muestra ningún error**: no se encontró el agente de appliance. Active **Scan appliances** para que exista.
- **`Error API cant create event: ...`**: falló la petición a la API de Pandora FMS. Compruebe **API Url**, que debe terminar en `/` (por ejemplo `https://<PANDORA_FMS_URL>/pandora_console/`), y el token.
- **Menos agentes de servidor de los esperados**: un servidor cuyos datos no se pudieron leer se omite sin mensaje.
- **`error with server: ...`, `Error appliances: ...`, `Error servers: ...`**: no se pudieron procesar los datos del servidor o de la appliance; el mensaje incluye la causa.

## Referencia

### Parámetros de la tarea

#### HP one view base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| IP | `_ip_` | string | — | Obligatorio. Dirección de la appliance HP OneView |
| User | `_user_` | string | — | Obligatorio |
| Password | `_password_` | password | — | Obligatorio |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de Tentacle |

#### HP one view Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Max threads | `_threads_` | number | `1` | Opcional. No lo utiliza esta versión |
| Use prefix | `_usePrefix_` | checkbox | desactivado | Habilita **Prefix** |
| Prefix | `_prefix_` | string | — | Opcional. Se muestra con **Use prefix** activado |
| Scan appliances | `_scanAppliances_` | checkbox | activado | Agente de appliance |
| Scan servers | `_scanServers_` | checkbox | activado | Agentes de servidor |
| Scan alerts | `_scanAlerts_` | checkbox | activado | Eventos a partir de alertas. Muestra los cuatro campos siguientes |
| API Url | `_apiUrl_` | string | — | Opcional en la consola, necesario para los eventos. URL base de la consola de Pandora FMS, terminada en `/` |
| API Token | `_apiToken_` | string | — | Opcional en la consola, necesario para los eventos. Token bearer de la API v2 de Pandora FMS |
| Server conf | `_serverConf_` | string | `/etc/pandora/pandora_server.conf` | Opcional. Fichero de configuración del servidor de Pandora FMS del que se leen los datos de la base de datos |
| Events ID group | `_eventsIdgroup_` | string | — | Opcional en la consola, necesario para los eventos. ID numérico del grupo de los eventos |

La llamada a la API que crea los eventos no valida los certificados TLS. El token de la API se guarda en la configuración de la tarea; utilice un token con los permisos mínimos necesarios para crear eventos.

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea, sin cabecera de sección.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_name` | vacío | Grupo de los agentes generados |
| `interval` | `300` | Intervalo de los agentes, en segundos |
| `transfer_mode` | `tentacle` | Modo de transferencia de los ficheros de datos |
| `tentacle_client` | `tentacle_client` | Ejecutable del cliente Tentacle |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `data_dir` | `/var/spool/pandora/data_in/` | Destino de los ficheros de datos en modo `local` |
| `prefix` | vacío | Prefijo de los alias de agente y de los nombres de módulo |
| `ip` | vacío | Dirección de la appliance HP OneView |
| `user` | vacío | Usuario de OneView |
| `password` | vacío | Contraseña de OneView |
| `server_conf` | `/etc/pandora/pandora_server.conf` | Fichero de configuración del servidor de Pandora FMS |
| `events_id_group` | vacío | ID del grupo de los eventos |
| `api_url` | vacío | URL de la consola de Pandora FMS, terminada en `/` |
| `token_api` | vacío | Token de la API v2 de Pandora FMS |
| `scan_alerts` | `1` | `1` crea eventos a partir de alertas; cualquier otro valor lo desactiva |
| `scan_appliances` | `1` | `1` crea el agente de appliance; cualquier otro valor lo desactiva |
| `scan_servers` | `1` | `1` crea los agentes de servidor; cualquier otro valor lo desactiva |

Ejemplo:

```ini
agents_group_name = <AGENT_GROUP>
interval          = 300
transfer_mode     = tentacle
prefix            = <PREFIX>
ip                = <ONEVIEW_HOST>
user              = <USERNAME>
password          = <PASSWORD>
tentacle_ip       = <TENTACLE_SERVER_IP>
tentacle_port     = 41121
server_conf       = /etc/pandora/pandora_server.conf
events_id_group   = <EVENTS_GROUP_ID>
api_url           = https://<PANDORA_FMS_URL>/pandora_console/
token_api         = <API_TOKEN>
scan_alerts       = 1
scan_appliances   = 1
scan_servers      = 1
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | HP One View |
| Identificador | `pandorafms.hp.oneview` |
| Versión | `1.0` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.hp.oneview](https://marketplace.pandorafms.com/entries/pandorafms.hp.oneview), actualizada el 2026-02-05 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
