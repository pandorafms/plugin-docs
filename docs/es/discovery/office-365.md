# Office 365 Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Office 365 monitoriza la salud y el licenciamiento de un tenant de Microsoft 365. Consulta la API de Microsoft Graph y convierte el resultado en agentes y módulos de Pandora FMS: el estado de cada servicio de Microsoft 365, las incidencias sin resolver de cada servicio, los avisos de servicio como entradas de log y el uso de cada licencia contratada.

Una tarea de Discovery genera hasta dos agentes:

- **Un agente de salud de servicios** con, para cada servicio de Microsoft 365, un módulo de estado y un módulo con sus incidencias sin resolver. Los avisos de servicio (mensajes de mantenimiento e incidencias) se envían al recolector de logs de Pandora FMS asociado a este agente.
- **Un agente de licencias** (opcional) con, para cada licencia contratada por el tenant, módulos de su estado y de las unidades habilitadas, consumidas y disponibles.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.office365`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Véase [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a `login.microsoftonline.com` y `graph.microsoft.com` | `Required` | El addon se autentica y consulta los datos mediante estos hosts |
| Aplicación de Microsoft Entra ID con los permisos indicados en [Permisos de Microsoft Graph](#permisos-de-microsoft-graph) | `Required` | Prerrequisito, no una declaración de compatibilidad |
| Versiones concretas de Pandora FMS | `Not validated` | El Marketplace muestra un aviso general para todas sus integraciones; no se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a los endpoints de Microsoft indicados.
2. **Una aplicación de Microsoft Entra ID** registrada en el tenant que se quiere monitorizar, con un secreto de cliente y los permisos de aplicación descritos a continuación.
3. **El ID de tenant, el ID de cliente y el secreto de cliente** de esa aplicación.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye su propio ejecutable, `bin/pandora_o365`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Registrar la aplicación en Microsoft Entra ID

El addon se autentica con el flujo de credenciales de cliente de OAuth 2.0, sin usuario conectado. Prepare la aplicación en el portal de Azure:

1. Abra Microsoft Entra ID y registre una aplicación nueva en **Registros de aplicaciones**. Regístrela en el tenant que quiere monitorizar.
2. En **Certificados y secretos**, cree un secreto de cliente y copie su valor de inmediato: Azure lo muestra una sola vez.
3. En la información general de la aplicación, copie el **ID de aplicación (cliente)** y el **ID de directorio (inquilino)**.
4. En **Permisos de API**, añada los permisos de aplicación de Microsoft Graph indicados a continuación y conceda el consentimiento de administrador.

![Información general de la aplicación de Microsoft Entra ID con el ID de aplicación (cliente) y el ID de directorio (inquilino)](../assets/images/discovery/office-365/entra-app-overview-ids.png)

<!-- SCREENSHOT NEEDED: Página de permisos de API de la aplicación con los permisos de aplicación de Microsoft Graph indicados a continuación y el consentimiento de administrador concedido. -->

### Permisos de Microsoft Graph

El addon solicita un token de aplicación con el ámbito `https://graph.microsoft.com/.default`, por lo que recibe los permisos de aplicación concedidos a la aplicación registrada. Cada conjunto de datos que lee queda cubierto por los siguientes permisos de aplicación de Microsoft Graph, según la documentación de Microsoft Graph de cada endpoint:

| Petición a Microsoft Graph | Se usa para | Permiso de aplicación |
|----------------------------|-------------|-----------------------|
| `/admin/serviceAnnouncement/healthOverviews` | Estado de los servicios e incidencias sin resolver | `ServiceHealth.Read.All` |
| `/admin/serviceAnnouncement/messages` | Avisos de servicio enviados como logs | `ServiceMessage.Read.All` |
| `/subscribedSkus` | Agente de licencias | `LicenseAssignment.Read.All` (la opción de menor privilegio que indica Microsoft; `Organization.Read.All` y `Directory.Read.All` también sirven) |

Conceda solo los permisos de las funciones que habilite: omita `ServiceMessage.Read.All` cuando **Logs** esté desactivado y `LicenseAssignment.Read.All` cuando la monitorización de licencias esté desactivada. No conceda las variantes `ReadWrite`.

El secreto de cliente es una credencial: guárdelo solo en la tarea y revóquelo en Microsoft Entra ID cuando deje de ser necesario.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.office365](https://marketplace.pandorafms.com/entries/pandorafms.office365)

Cárguelo en Pandora FMS. Una vez cargado, **Office 365** está disponible al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree una tarea de Discovery y elija **Office 365**. La consola presenta los campos en dos pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Office365 base** — acceso al tenant y destino de los datos:

    - **Client ID**, **Tenant ID** y **Secret**: los valores de la aplicación de Microsoft Entra ID. La consola trata los tres como campos de contraseña.
    - **Tentacle IP** y **Tentacle port**: destino de los datos de los agentes generados. Los valores por defecto son `127.0.0.1` y `41121`; rara vez hay que cambiarlos.

    ![Paso Office365 base del asistente](../assets/images/discovery/office-365/office365-base-step.png)

2. **Office365 Detailed** — agentes y datos que se recogen:

    - **Agent Name**: nombre del agente de salud de servicios.
    - **Use prefix** y **Prefix**: prefijo añadido al nombre del agente y a sus módulos. **Prefix** solo se muestra cuando **Use prefix** está activado.
    - **Logs**: enviar los avisos de servicio al recolector de logs de Pandora FMS.
    - **utf8**: codificar el valor de los módulos de incidencias como texto UTF-8.
    - **Not data**: no crear los módulos de estado e incidencias.
    - **Activate licensing monitoring**, **Licensing agent name** y **Prefix for licensing data**: crear el agente de licencias. Los dos últimos solo se muestran cuando la monitorización de licencias está activada.
    - **Max threads**: se muestra por compatibilidad; esta versión del addon no lo utiliza.

    ![Paso Office365 Detailed del asistente](../assets/images/discovery/office-365/office365-detailed-step.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que esta crea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que se completa informa de **Total agents** y **Total modules**. **Total agents** es `2` con la monitorización de licencias activada y `1` en caso contrario. **Total modules** suma los módulos de estado, incidencias, logs y licencias generados.

    ![Resumen de una tarea de Discovery de Office 365 con Total agents y Total modules](../assets/images/discovery/office-365/office365-task-summary.png)

2. **Los agentes.** El agente de salud de servicios, con el nombre de **Agent Name** (por defecto `Pandora_O365`) y, con la monitorización de licencias activada, el agente de licencias (por defecto `Pandora_O365_licensing`).
3. **Los módulos.** El agente de salud de servicios tiene un módulo `<servicio>_status` y otro `<servicio>_active_issues` por cada servicio de Microsoft 365; el agente de licencias tiene los módulos descritos en [Interpretar los resultados](#interpretar-los-resultados). Las entradas de log aparecen en el recolector de logs con el nombre del servicio.

Cuando un paso falla, la tarea registra el error en su información de ejecución; véase [Solución de problemas](#solucion-de-problemas).

## Interpretar los resultados

### Agentes generados

| Agente | Nombre y alias | Grupo | Se crea cuando |
|--------|----------------|-------|----------------|
| Agente de salud de servicios | `<Prefix><Agent Name>` | Grupo de la tarea | Siempre |
| Agente de licencias | `<Prefix for licensing data><Licensing agent name>` | Grupo de la tarea | **Activate licensing monitoring** está activado |

Ambos agentes se refrescan con el intervalo de la tarea y tienen la descripción `Agent generated by pandora_o365 plugin`. Los dos prefijos son independientes: **Prefix** no se aplica al agente de licencias.

### Módulos por agente

**Agente de salud de servicios**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `<Prefix><id de servicio>_status` | `generic_data_string` | **Not data** desactivado | Estado del servicio de Microsoft 365 según Microsoft Graph. El módulo pasa a `warning` cuando el estado coincide con `investigating`, `restoringService` o `extendedRecovery`, y a `critical` cuando coincide con `serviceDegradation` o `serviceInterruption` |
| `<Prefix><id de servicio>_active_issues` | `generic_data_string` | **Not data** desactivado | Identificador y título de cada incidencia sin resolver del servicio, concatenados sin separador, por lo que las incidencias consecutivas quedan unidas; `None` cuando el servicio no tiene incidencias sin resolver. Descripción: `<servicio> Issues Ids` |
| Entradas de log | Recolector de logs | **Logs** activado | Una entrada por aviso de servicio leído a partir del elemento 101, con el origen `<Prefix>_<servicio>`. El contenido es el aviso convertido a texto plano. La colección no se pagina, por lo que los 100 primeros avisos nunca se recogen y un tenant con menos de 100 avisos no produce entradas |

`<id de servicio>` es el identificador del servicio que devuelve Microsoft Graph, por ejemplo el de Exchange Online o Microsoft Teams.

**Agente de licencias**

Para cada licencia (SKU) contratada por el tenant, el agente tiene los siguientes módulos. `<nombre>` es el part number de la licencia que devuelve Microsoft Graph y la descripción de cada módulo es el identificador de la licencia.

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<Prefix><nombre>` | `generic_data_string` | Estado de capacidad de la licencia |
| `<Prefix><nombre> consumedUnits` | `generic_data` | Unidades consumidas |
| `<Prefix><nombre> Units enabled` | `generic_data` | Unidades habilitadas |
| `<Prefix><nombre> Units lockedOut` | `generic_data` | Unidades bloqueadas |
| `<Prefix><nombre> Units suspended` | `generic_data` | Unidades suspendidas |
| `<Prefix><nombre> Units warning` | `generic_data` | Unidades en estado de advertencia |
| `<Prefix><nombre> Consumed Units %` | `generic_data` | Porcentaje de unidades habilitadas consumidas, redondeado a dos decimales, en `%`. Es `0` cuando no hay unidades habilitadas |
| `<Prefix><nombre> Units Available` | `generic_data` | Unidades habilitadas menos unidades consumidas |

Aquí `<Prefix>` es **Prefix for licensing data**.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta de un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_o365 --conf <PATH_TO_CONFIG>
```

Envía un fichero de datos por agente con el modo de transferencia configurado e imprime un resumen JSON con los recuentos **Total agents** y **Total modules**. Cuando se producen errores, el JSON incluye además una clave `info` con los mensajes.

El fichero de configuración contiene el secreto de cliente. Protéjalo con permisos restrictivos y no lo conserve tras la prueba.

## Solución de problemas

El addon no tiene opción de salida detallada ni de depuración. Su canal de diagnóstico es la información registrada en el resultado de ejecución de la tarea.

- **`HTTP error: ... on https://login.microsoftonline.com/...`**: Microsoft Entra ID rechazó la autenticación. Compruebe el ID de tenant, el ID de cliente y el secreto de cliente, y que el secreto no haya caducado.
- **`Request error: ...`**: el servidor de Discovery no alcanza `login.microsoftonline.com`. Compruebe la conectividad saliente, el DNS y los proxies o cortafuegos.
- **`Error requesting url: ... (<estado>) on https://graph.microsoft.com/...`**: Microsoft Graph rechazó una petición de datos. Un estado `403` puede indicar que la aplicación carece del permiso de ese endpoint o que no se concedió el consentimiento de administrador; véase [Permisos de Microsoft Graph](#permisos-de-microsoft-graph). El mensaje indica el endpoint.
- **`error with status data: ...`, `error logs data: ...` o `error with licensing data: ...`**: falló la lectura o el procesado de ese conjunto de datos. El texto del error se añade al mensaje.
- **`error with accounts data: ...`**: no se puede leer el fichero de configuración. Solo aparece en la ejecución manual.
- **No hay módulos `_status` ni `_active_issues`**: **Not data** está activado.
- **No hay agente de licencias**: **Activate licensing monitoring** está desactivado.
- **No hay entradas de log**: **Logs** está desactivado, Microsoft Graph no devolvió avisos a partir del elemento 101 o el tenant tiene menos de 100 avisos.
- **Los valores de incidencias aparecen como una cadena de bytes**: **utf8** está desactivado. Actívelo salvo que el entorno requiera bytes sin procesar.

## Referencia

### Parámetros de la tarea

#### Office365 base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Client ID | `_clientid_` | contraseña | vacío | Obligatorio. ID de aplicación (cliente) |
| Tenant ID | `_tenantid_` | contraseña | vacío | Obligatorio. ID de directorio (inquilino) |
| Secret | `_secret_` | contraseña | vacío | Obligatorio. Valor del secreto de cliente |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |

#### Office365 Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Max threads | `_threads_` | número | `1` | Opcional. No lo utiliza esta versión del addon |
| Agent Name | `_agentname_` | cadena | `Pandora_O365` | Nombre y alias del agente de salud de servicios |
| Use prefix | `_usePrefix_` | casilla | desactivado | Muestra **Prefix** |
| Prefix | `_prefix_` | cadena | vacío | Opcional. Se muestra con **Use prefix** activado. Se antepone al nombre del agente, a los nombres de módulo y al origen del log |
| Logs | `_logs_` | casilla | activado | Enviar los avisos de servicio al recolector de logs |
| utf8 | `_utf_` | casilla | activado | Codificar el valor de las incidencias como texto UTF-8; desactivado, el valor se escribe como bytes sin procesar |
| Not data | `_activemonitoring_` | casilla | desactivado | Activado, no se crean los módulos de estado e incidencias |
| Activate licensing monitoring | `_licensing_` | casilla | activado | Crear el agente de licencias |
| Licensing agent name | `_agentnameLicensing_` | cadena | `Pandora_O365_licensing` | Opcional. Se muestra con la monitorización de licencias activada |
| Prefix for licensing data | `_prefixLicensing_` | cadena | vacío | Opcional. Se muestra con la monitorización de licencias activada |

### Fichero de configuración

Se usa en la ejecución manual. Una pareja `clave = valor` por línea; las claves ausentes toman el valor por defecto indicado aquí. Una opción numérica que no sea un número se lee como `0`; `1` activa y `0` desactiva.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_name` | vacío | Grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `transfer_mode` | `tentacle` | Modo de transferencia de datos. La tarea de Discovery siempre usa `tentacle` |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `client_id` | vacío | ID de aplicación (cliente) |
| `tenant_id` | vacío | ID de directorio (inquilino) |
| `secret` | vacío | Valor del secreto de cliente |
| `agent_name` | `Pandora_O365_` | Nombre y alias del agente de salud de servicios |
| `prefix` | vacío | Prefijo del nombre del agente, de los nombres de módulo y del origen del log |
| `logs` | `1` | Crear las entradas de log |
| `utf8` | `1` | Codificar el valor de las incidencias como texto UTF-8 |
| `no_data` | `1` | Con `1`, no se crean los módulos de estado e incidencias. Use `0` para crearlos |
| `licensing` | `1` | Crear el agente de licencias |
| `agent_name_licensing` | `Pandora_O365_licensing` | Nombre y alias del agente de licencias |
| `prefix_licensing` | vacío | Prefijo del nombre del agente de licencias y de sus módulos |

El valor por defecto de `agent_name` y de `no_data` difiere entre la tarea de Discovery y la ejecución manual: la tarea usa `Pandora_O365` y `no_data = 0`, mientras que un fichero de configuración sin esas claves usa los valores indicados arriba.

Ejemplo:

```ini
agents_group_name    = <GROUP_NAME>
interval             = 300
transfer_mode        = tentacle
tentacle_ip          = <TENTACLE_SERVER_IP>
tentacle_port        = 41121
client_id            = <CLIENT_ID>
tenant_id            = <TENANT_ID>
secret               = <CLIENT_SECRET>
agent_name           = Pandora_O365
prefix               =
logs                 = 1
utf8                 = 1
no_data              = 0
licensing            = 1
agent_name_licensing = Pandora_O365_licensing
prefix_licensing     =
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Office 365 |
| Identificador | `pandorafms.office365` |
| Versión | `1.1` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.office365](https://marketplace.pandorafms.com/entries/pandorafms.office365), última actualización 2026-02-05 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
