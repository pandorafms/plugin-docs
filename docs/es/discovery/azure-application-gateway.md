# Azure Application Gateway Discovery

*Última actualización del artículo: 2026-09-16.*

## Qué monitoriza

El plugin de Discovery de Azure Application Gateway descubre los Azure Application Gateways de una suscripción de Microsoft Azure y convierte sus métricas de Azure Monitor en agentes y módulos de Pandora FMS: rendimiento, contadores de peticiones y de salud del backend, latencia, tráfico, seguridad, capacidad, Web Application Firewall (WAF), actividad WebSocket y un recuento por Application Gateway.

Por defecto crea **un agente por Application Gateway**, con el nombre del Application Gateway y un prefijo opcional. También puede consolidar todos los Application Gateways descubiertos en un único agente. Cada agente lleva un módulo de disponibilidad y un módulo por métrica habilitada.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.azure.gateway`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Microsoft Azure Network y Azure Monitor | `Requerido` | El plugin enumera los Application Gateways con la API de Network y lee sus métricas con la API de Monitor |
| Una entidad de servicio de Microsoft Entra capaz de listar Application Gateways y leer sus métricas de Azure Monitor | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure) |
| Un grupo de agentes de Pandora FMS con ID mayor que `0` | `Requerido` | El grupo `All` tiene ID `0` y no se puede usar |
| Nubes de Azure soberanas o personalizadas | `Sin validar` | Los endpoints son los públicos de Azure; ningún registro de pruebas establece su funcionamiento contra una nube no pública |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga Application Gateways.
3. **Una credencial de Azure** guardada en el almacén de credenciales de Pandora FMS, o sus valores suministrados directamente para una ejecución manual.
4. **Un grupo de agentes válido** para la tarea. El grupo `All` no es válido, porque su ID es `0`.

El plugin se distribuye como un ejecutable autocontenido: la aplicación Discovery empaquetada incluye `bin/pandora_azure_gateway`, por lo que no es necesario instalar ningún runtime adicional en el servidor de Pandora FMS ni para una ejecución manual.

### Preparar el acceso a Azure

Cree una entidad de servicio de Microsoft Entra que pueda enumerar los Application Gateways y leer sus métricas de Azure Monitor, sobre la suscripción o el Resource Group que se vaya a descubrir. El plugin lista los Application Gateways con la API de Azure Network y lee las métricas con la API de Azure Monitor, por lo que la entidad necesita acceso de lectura a ambas. No conceda un rol más amplio del que exige su política.

Guarde su **Client ID**, **Application secret**, **Tenant or domain name** y **Subscription id** como una credencial de Azure en el almacén de credenciales de Pandora FMS, de modo que la tarea haga referencia a la credencial en lugar de transportar el secreto.

En la mayoría de entornos basta con un rol `Reader` sobre la suscripción o el Resource Group. La entidad se crea desde la CLI de Azure con:

```bash
az ad sp create-for-rbac \
  --name pandora-azure-application-gateway-discovery \
  --role Reader \
  --scopes /subscriptions/<SUBSCRIPTION_ID>
```

El comando devuelve los valores que hay que guardar, asignados así:

```text
tenant       -> Tenant or domain name
appId        -> Client ID
password     -> Application secret
subscription -> Subscription id
```

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Azure Application Gateway** aparece en la categoría **Cloud** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure Application Gateway**. El primer paso genérico del asistente define la tarea; el paquete añade **Azure Base**, **Application Gateway Options** y **Metrics**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo, servidor e intervalo. El grupo debe tener un ID mayor que `0`; `All` no se puede usar. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure Base.** Qué suscripción leer y cuánto de ella:

- **Azure credentials** selecciona la credencial de Azure guardada. La credencial contiene el Client ID, el Application secret, el Tenant or domain name y el Subscription ID.
- **Custom Resource Group** limita el descubrimiento a un único Resource Group, y **Resource group** lo nombra exactamente. Aquí no se aceptan expresiones regulares.

![Paso Azure Base del asistente con el selector de credencial, el conmutador Custom Resource Group y el campo Resource group.](../assets/images/discovery/azure-application-gateway/azure-base.png)

**Paso 3 — Application Gateway Options.** Distribución de agentes, caché de descubrimiento y diagnóstico:

- **Target agent** solo se usa cuando **Create one agent per Application Gateway** está deshabilitado.
- **Scan Application Gateways** consulta Azure para descubrir los Application Gateways actuales; cuando está deshabilitado se reutiliza el archivo de entidades en caché.
- **Create one agent per Application Gateway** decide la distribución de agentes: un agente por recurso, o todos los módulos en el único **Target agent**.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS.
- **Application Gateway agent prefix** nombra los agentes por Application Gateway.
- **Modules prefix** se antepone a todos los nombres de módulo generados.
- **Enable entities file re-scan interval** y **Entities re-scan interval** controlan cuánto tiempo se reutiliza la caché descubierta antes de reconstruirse.
- **Debug** revela la opción de mock local, que existe solo para pruebas.

<!-- SCREENSHOT NEEDED: Paso Application Gateway Options del asistente con los campos de distribución de agentes, caché y Debug en el orden del plugin final (Target agent, Scan Application Gateways, Create one agent per Application Gateway, Agent autodisable mode, prefijos, intervalo de caché, Debug y Mock Azure API URL). -->

**Paso 4 — Metrics.** Qué familias de métricas se recogen:

- **Metrics time window** es el rango consultado en Azure Monitor y **Azure metric interval** es la granularidad temporal.
- **Metric timeout** acota cada petición y **Max retries** cubre los errores temporales de Azure y las respuestas HTTP 429.
- Un conmutador por familia de métricas: **Performance modules**, **Request modules**, **Backend modules**, **Latency modules**, **Traffic modules**, **Security modules**, **Capacity modules**, **WAF modules**, **WebSocket modules** y **Application Gateway count module**.
- **Modules allow regexp** y **Modules deny regexp** filtran los nombres finales de los módulos.

![Paso Metrics del asistente con los conmutadores de familias de métricas, los campos de tiempo, intervalo, timeout y reintentos, y las expresiones regulares de allow y deny.](../assets/images/discovery/azure-application-gateway/metrics.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de `application_gateways_discovered`, `application_gateways_vanished`, `modules`, `errors`, `unsupported_metrics` y `scan_source`. Espere un agente por Application Gateway descubierto, o un único **Target agent** cuando la creación por Application Gateway está deshabilitada.

2. **Los agentes.** Nombrados `<Application Gateway agent prefix><nombre del Application Gateway>` por defecto, por lo que `Azure Application Gateway agw-standard-v1`. Cada uno informa de `Azure` como sistema operativo y de `sku.name sku.tier` como versión, y hereda el grupo y el intervalo de la tarea.

3. **`Application Gateway Connection`** es `1` en todo Application Gateway descubierto. Un `0` significa que el Application Gateway está en la caché pero ya no es descubrible — consulte [Solución de problemas](#solucion-de-problemas).

4. **Los módulos de métricas** de cada familia habilitada, para aquellas métricas que Azure Monitor realmente informa del recurso.

![Agentes gestionados creados por una tarea de Azure Application Gateway, uno por Application Gateway descubierto.](../assets/images/discovery/azure-application-gateway/managed-agents.png)

Si no aparece ningún agente, lo primero que hay que revisar son la credencial o sus permisos.

## Interpretar los resultados

### Distribución de agentes

**Con Create one agent per Application Gateway habilitado**, que es el valor por defecto, el plugin crea un agente por Application Gateway, llamado `<Application Gateway agent prefix><nombre del Application Gateway>`. Se inserta un separador cuando el prefijo no termina en espacio, guion o guion bajo, por lo que un prefijo de `Azure Application Gateway` se comporta como `Azure Application Gateway `.

**Con él deshabilitado**, todos los módulos van al único **Target agent** y el nombre del Application Gateway se antepone a cada nombre de módulo. Esto importa para el filtrado: las expresiones regulares allow y deny se evalúan contra el nombre *final* del módulo, que en modo consolidado incluye ese prefijo del Application Gateway.

Los agentes generados informan de `Azure` como sistema operativo, heredan el grupo y el intervalo de la tarea, y se crean en el modo `2` de Pandora FMS cuando **Agent autodisable mode** está habilitado, o en el modo `1` cuando está deshabilitado. La dirección del agente es el nombre del Application Gateway y su descripción es el ID del recurso de Azure.

### Caché de descubrimiento y recursos desaparecidos

El plugin mantiene una caché de entidades ligada a la tarea en `entities_list`, sembrada desde la API de Application Gateway y reutilizada entre ejecuciones. La caché está acotada por tarea, de modo que dos tareas configuradas sobre la misma suscripción no comparten sus entidades descubiertas.

`Application Gateway Connection` se crea siempre, como `generic_proc`, con valor `1` para un Application Gateway descubierto. Cuando un Application Gateway en caché deja de ser descubrible, su agente se conserva y este módulo informa de `0` hasta que la entidad se descarta en una reconstrucción de la caché.

### Qué se crea

`Application Gateway Connection` es el único módulo `generic_proc`; su descripción registra el Resource Group y el SKU. El resto es `generic_data`, agrupado por la opción que lo habilita:

| Habilitado por | Qué se obtiene |
| --- | --- |
| Performance modules | `CPU Utilization`, `Current Connections`, `Throughput` y `New Connections Per Second` |
| Request modules | `Failed Requests`, `HTTP Status` y `Total Requests` |
| Backend modules | `Healthy Host Count`, `Unhealthy Host Count`, `Average Request Count Per Healthy Host` y `Backend HTTP Status` |
| Latency modules | `Backend Connect Time`, `Backend First Byte Response Time`, `Backend Last Byte Response Time`, `Application Gateway Total Time` y `Client RTT` |
| Traffic modules | `Bytes Sent` y `Bytes Received` |
| Security modules | `TLS Protocol`, `Backend TLS Negotiation Error` y `Rejected Connections` |
| Capacity modules | `Compute Units`, `Capacity Units`, `Estimated Billed Capacity Units` y `Fixed Billable Capacity Units` |
| WAF modules | `WAF Matched Count`, `WAF Blocked Requests`, `WAF Blocked Count`, `WAF Total Requests`, `WAF Security Rule`, `WAF Custom Rule`, `WAF Bot Protection`, `WAF JS Challenge Request Count`, `WAF Penalty Box Hits`, `WAF Penalty Box Size` y `WAF Captcha Challenge Request Count` |
| WebSocket modules | `WebSocket Active Connections` y `WebSocket Specific Close Status Code` |
| Application Gateway count module | `Application Gateway Count` |

Todos los módulos se leen de Azure Monitor y llevan la descripción `Azure metric <MetricName> (<Aggregation>)`. Las métricas de capacidad y `New Connections Per Second` solo se recogen en SKUs v2, y las métricas WAF solo en SKUs WAF; además, el plugin pregunta a Azure Monitor qué métricas hay disponibles para el recurso y descarta el resto. Una métrica que Azure rechaza se reintenta por separado y, si sigue fallando, se cuenta en `unsupported_metrics` en lugar de abortar la ejecución. El inventario exhaustivo de módulos está en [Módulos generados](#modulos-generados).

![Módulos creados en un agente de Azure Application Gateway.](../assets/images/discovery/azure-application-gateway/agent-modules.png)

![Lista de módulos con los últimos valores recogidos de Azure Monitor.](../assets/images/discovery/azure-application-gateway/module-list.png)

## Solución de problemas

- **La tarea falla por el grupo** — el grupo de agentes debe tener un ID mayor que `0`. `All` es el grupo `0` y no se puede usar.
- **No se descubre ningún Application Gateway** — compruebe la entidad de servicio en este orden: los valores de la credencial, después que pueda listar los Application Gateways y leer sus métricas, y después si **Custom Resource Group** está limitando la búsqueda.
- **`tenant_id, client_id and client_secret are required`** — no se ha resuelto ninguna credencial de Azure utilizable. Seleccione una credencial de Azure válida en **Azure Base** o, para una ejecución manual, proporcione `credentials` o las claves `tenant_id`, `client_id` y `client_secret`.
- **Un agente sobrevive con `Application Gateway Connection` a `0`** — el Application Gateway está en la caché de entidades pero ya no es descubrible, porque se eliminó, se renombró o salió del ámbito configurado. El agente se conserva hasta que la caché se reconstruye, lo que ocurre tras **Entities re-scan interval**.
- **Faltan módulos esperados** — las expresiones regulares allow y deny se evalúan contra el nombre final del módulo. En modo consolidado ese nombre lleva el nombre del Application Gateway, por lo que una expresión escrita para el modo por Application Gateway no coincidirá. Las métricas específicas de SKU que Azure Monitor no informa del recurso también se descartan y se cuentan en `unsupported_metrics`.
- **Azure rechaza una petición de métricas con HTTP 400 `Failed to find metric configuration`** — una métrica del lote no es válida para ese SKU. El plugin reintenta las métricas individualmente y descarta la no soportada, de modo que la ejecución termina bien; consulte `unsupported_metrics` para ver la lista.
- **Las peticiones agotan el tiempo o fallan con un estado HTTP reintentable** — suba **Metric timeout** o **Max retries**. El plugin reintenta los estados HTTP de Azure 429, 500, 502, 503 y 504 hasta **Max retries** veces, respetando la cabecera `Retry-After` cuando está presente.
- **Debug, Mock Azure API URL** existen para apuntar el plugin a un mock local durante las pruebas. Deje **Debug** desactivado en entornos reales.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Azure Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Azure credentials | `_credentials_` | select | — | Credencial de Azure del almacén de credenciales de Pandora FMS. Obligatorio |
| Custom Resource Group | `_customresourcegroup_` | checkbox | off | Limita el descubrimiento a un Resource Group |
| Resource group | `_resourcegroup_` | string | — | Nombre exacto del Resource Group. Solo se muestra cuando la opción anterior está habilitada; no es una expresión regular |

#### Application Gateway Options

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Target agent | `_targetagent_` | string | `Azure Application Gateways` | Agente usado en modo consolidado. Solo se usa cuando **Create one agent per Application Gateway** está deshabilitado |
| Scan Application Gateways | `_scanagw_` | checkbox | on | Consulta Azure para descubrir los Application Gateways actuales |
| Create one agent per Application Gateway | `_agentperagw_` | checkbox | on | Deshabilitado envía todos los módulos a **Target agent** |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` cuando está habilitado, en el modo `1` en caso contrario |
| Application Gateway agent prefix | `_agwagentprefix_` | string | `Azure Application Gateway ` | Prefijo de los agentes por Application Gateway |
| Modules prefix | `_modulesprefix_` | string | — | Prefijo antepuesto a todos los nombres de módulo generados |
| Enable entities file re-scan interval | `_enableentitiesinterval_` | checkbox | on | Reutiliza la caché descubierta hasta que el intervalo expira |
| Entities re-scan interval | `_entitiesinterval_` | select | `3600` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Debug | `_debug_` | checkbox | off | Revela la opción de mock local, que existe solo para pruebas |
| Mock Azure API URL | `_mockapiurl_` | string | — | URL base del mock local. Solo se muestra cuando **Debug** está habilitado; déjelo vacío en entornos reales |

#### Metrics

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Metrics time window | `_timewindow_` | select | `300` | Rango consultado en Azure Monitor para cada petición, en segundos |
| Azure metric interval | `_metricinterval_` | select | `PT5M` | Granularidad temporal de Azure Monitor (`PT1M`, `PT5M`, `PT15M`, `PT30M`, `PT1H`, `PT6H`, `PT12H`, `P1D`) |
| Metric timeout | `_metrictimeout_` | number | `30` | Tiempo de espera de la petición en segundos; `0` o negativo usa `30` |
| Max retries | `_maxretries_` | number | `2` | Reintentos para errores temporales de Azure y respuestas HTTP 429 |
| Performance modules | `_checkperformance_` | checkbox | on | `CPU Utilization`, `Current Connections`, `Throughput` y `New Connections Per Second` |
| Request modules | `_checkrequest_` | checkbox | on | `Failed Requests`, `HTTP Status` y `Total Requests` |
| Backend modules | `_checkbackend_` | checkbox | on | `Healthy Host Count`, `Unhealthy Host Count`, `Average Request Count Per Healthy Host` y `Backend HTTP Status` |
| Latency modules | `_checklatency_` | checkbox | on | `Backend Connect Time`, `Backend First Byte Response Time`, `Backend Last Byte Response Time`, `Application Gateway Total Time` y `Client RTT` |
| Traffic modules | `_checktraffic_` | checkbox | on | `Bytes Sent` y `Bytes Received` |
| Security modules | `_checksecurity_` | checkbox | on | `TLS Protocol`, `Backend TLS Negotiation Error` y `Rejected Connections` |
| Capacity modules | `_checkcapacity_` | checkbox | on | `Compute Units`, `Capacity Units`, `Estimated Billed Capacity Units` y `Fixed Billable Capacity Units`. SKUs v2 |
| WAF modules | `_checkwaf_` | checkbox | on | Métricas WAF matched, blocked, reglas, protección de bots, challenge y penalty box. SKUs WAF |
| WebSocket modules | `_checkwebsocket_` | checkbox | on | `WebSocket Active Connections` y `WebSocket Specific Close Status Code` |
| Application Gateway count module | `_checkcount_` | checkbox | on | `Application Gateway Count` |
| Modules allow regexp | `_moduleallowlist_` | textarea | — | Una expresión por línea. Solo se conservan los nombres de módulo que coinciden con al menos una |
| Modules deny regexp | `_moduledenylist_` | textarea | — | Una expresión por línea. Los nombres de módulo coincidentes se excluyen. Deny tiene prioridad sobre allow |

### Claves del archivo de configuración

La tarea de Discovery construye este archivo a partir de sus propios campos; una ejecución manual lo suministra con `--conf`. Las listas allow y deny se pasan como rutas de archivo con las claves `module_allow_list_file` y `module_deny_list_file`, una expresión por línea.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `agents_group_id` | ID de grupo de Pandora FMS asignado a los agentes generados. Debe ser mayor que `0` | Obligatorio |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` en ejecuciones manuales |
| `credentials` | Credencial de Azure codificada en base64 generada por Pandora FMS | Vacío |
| `subscription_id`, `tenant_id`, `client_id`, `client_secret` | Valores de credencial manuales, usados cuando no se proporciona `credentials` | Vacío |
| `resource_group` | Limita el descubrimiento a un Resource Group exacto | Vacío |
| `target_agent` | Agente usado en modo consolidado | `Azure Application Gateways` |
| `agent_per_application_gateway` | Crea un agente por Application Gateway cuando está habilitado | `1` |
| `agent_autodisable` | Usa el modo `2` de Pandora FMS cuando está habilitado y el modo `1` en caso contrario | `0` |
| `application_gateway_agent_prefix` | Prefijo de los agentes por Application Gateway | `Azure Application Gateway ` |
| `modules_prefix` | Prefijo de todos los nombres de módulo generados | Vacío |
| `scan_application_gateways` | Consulta Azure para descubrir los Application Gateways | `1` |
| `entities_list` | Ruta de la caché de entidades de Application Gateway | Vacío en ejecuciones manuales |
| `task_md5` | Identificador de la tarea que acota la caché de entidades a esta tarea | Vacío en ejecuciones manuales |
| `enable_entities_interval` | Conserva las entidades en caché hasta que el intervalo configurado expira | `1` |
| `entities_interval` | Intervalo de reconstrucción de la caché de entidades en segundos | `3600` |
| `time_window` | Rango consultado en Azure Monitor, en segundos | `300` |
| `metric_interval` | Granularidad temporal de Azure Monitor | `PT5M` |
| `metric_timeout` | Tiempo de espera de la petición a Azure en segundos | `30` |
| `max_retries` | Reintentos para errores de Azure reintentables y HTTP 429 | `2` |
| `output_format` | Formato de salida, `json` o `xml` | `json` |
| `module_allow_list` / `module_allow_list_file` | Expresiones regulares allow de módulos, en línea o en archivo | Vacío |
| `module_deny_list` / `module_deny_list_file` | Expresiones regulares deny de módulos, en línea o en archivo | Vacío |
| `check_performance_modules` | Habilita los módulos de rendimiento | `1` |
| `check_request_modules` | Habilita los módulos de peticiones | `1` |
| `check_backend_modules` | Habilita los módulos del backend | `1` |
| `check_latency_modules` | Habilita los módulos de latencia | `1` |
| `check_traffic_modules` | Habilita los módulos de tráfico | `1` |
| `check_security_modules` | Habilita los módulos de seguridad | `1` |
| `check_capacity_modules` | Habilita los módulos de capacidad | `1` |
| `check_waf_modules` | Habilita los módulos WAF | `1` |
| `check_websocket_modules` | Habilita los módulos WebSocket | `1` |
| `check_application_gateway_count` | Habilita el módulo de recuento de Application Gateways | `1` |
| `mock_api_url` | URL base del mock local. Solo para pruebas | Vacío |

El plugin reintenta los estados HTTP de Azure `429`, `500`, `502`, `503` y `504` hasta **Max retries** veces, respetando la cabecera `Retry-After` cuando está presente; el número de reintentos es configurable mediante **Max retries**.

### Ejecución en línea de comandos

El plugin lee un único archivo de configuración. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de tarea.

```bash
./pandora_azure_gateway --conf <PATH_TO_CONFIG>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta obligatoria al archivo de configuración |
| `--version` | Muestra la versión del plugin y termina |

Un archivo de configuración mínimo para una ejecución manual:

```ini
[CONF]
subscription_id=<SUBSCRIPTION_ID>
tenant_id=<TENANT_ID>
client_id=<CLIENT_ID>
client_secret=<CLIENT_SECRET>
agents_group_id=<GROUP_ID>
```

Ese archivo contiene una credencial en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin, manténgalo fuera de directorios compartidos y del control de versiones, y prefiera el almacén de credenciales de Pandora FMS para las ejecuciones de tarea, donde la tarea hace referencia a la credencial en lugar de transportarla.

### Módulos generados

Cada módulo lleva el prefijo del nombre del Application Gateway cuando **Create one agent per Application Gateway** está deshabilitado, y el **Modules prefix** cuando está definido.

**Siempre se crea**

- `Application Gateway Connection`: `generic_proc`, `1` para un Application Gateway descubierto. La descripción es el Resource Group y el SKU.

**Módulos de rendimiento**

- `CPU Utilization`: `generic_data`, métrica de Azure `CpuUtilization`, agregación Average.
- `Current Connections`: `generic_data`, métrica de Azure `CurrentConnections`, agregación Average.
- `Throughput`: `generic_data`, métrica de Azure `Throughput`, agregación Average.
- `New Connections Per Second`: `generic_data`, métrica de Azure `NewConnectionsPerSecond`, agregación Average. SKUs v2.

**Módulos de peticiones**

- `Failed Requests`: `generic_data`, métrica de Azure `FailedRequests`, agregación Total.
- `HTTP Status`: `generic_data`, métrica de Azure `HttpStatus`, agregación Total.
- `Total Requests`: `generic_data`, métrica de Azure `TotalRequests`, agregación Total.

**Módulos del backend**

- `Healthy Host Count`: `generic_data`, métrica de Azure `HealthyHostCount`, agregación Average.
- `Unhealthy Host Count`: `generic_data`, métrica de Azure `UnhealthyHostCount`, agregación Average.
- `Average Request Count Per Healthy Host`: `generic_data`, métrica de Azure `AvgRequestCountPerHealthyHost`, agregación Average.
- `Backend HTTP Status`: `generic_data`, métrica de Azure `BackendHttpStatus`, agregación Total.

**Módulos de latencia**

- `Backend Connect Time`: `generic_data`, métrica de Azure `BackendConnectTime`, agregación Average.
- `Backend First Byte Response Time`: `generic_data`, métrica de Azure `BackendFirstByteResponseTime`, agregación Average.
- `Backend Last Byte Response Time`: `generic_data`, métrica de Azure `BackendLastByteResponseTime`, agregación Average.
- `Application Gateway Total Time`: `generic_data`, métrica de Azure `ApplicationGatewayTotalTime`, agregación Average.
- `Client RTT`: `generic_data`, métrica de Azure `ClientRTT`, agregación Average.

**Módulos de tráfico**

- `Bytes Sent`: `generic_data`, métrica de Azure `BytesSent`, agregación Total.
- `Bytes Received`: `generic_data`, métrica de Azure `BytesReceived`, agregación Total.

**Módulos de seguridad**

- `TLS Protocol`: `generic_data`, métrica de Azure `TlsProtocol`, agregación Total.
- `Backend TLS Negotiation Error`: `generic_data`, métrica de Azure `BackendTlsNegotiationError`, agregación Total.
- `Rejected Connections`: `generic_data`, métrica de Azure `RejectedConnections`, agregación Total.

**Módulos de capacidad**

- `Compute Units`: `generic_data`, métrica de Azure `ComputeUnits`, agregación Average. SKUs v2.
- `Capacity Units`: `generic_data`, métrica de Azure `CapacityUnits`, agregación Average. SKUs v2.
- `Estimated Billed Capacity Units`: `generic_data`, métrica de Azure `EstimatedBilledCapacityUnits`, agregación Average. SKUs v2.
- `Fixed Billable Capacity Units`: `generic_data`, métrica de Azure `FixedBillableCapacityUnits`, agregación Average. SKUs v2.

**Módulos WAF**

- `WAF Matched Count`: `generic_data`, métrica de Azure `WafMatchedCount`, agregación Total. SKUs WAF.
- `WAF Blocked Requests`: `generic_data`, métrica de Azure `WafBlockedRequests`, agregación Total. SKUs WAF.
- `WAF Blocked Count`: `generic_data`, métrica de Azure `WafBlockedCount`, agregación Total. SKUs WAF.
- `WAF Total Requests`: `generic_data`, métrica de Azure `WafTotalRequests`, agregación Total. SKUs WAF.
- `WAF Security Rule`: `generic_data`, métrica de Azure `WafSecRule`, agregación Total. SKUs WAF.
- `WAF Custom Rule`: `generic_data`, métrica de Azure `WafCustomRule`, agregación Total. SKUs WAF.
- `WAF Bot Protection`: `generic_data`, métrica de Azure `WafBotProtection`, agregación Total. SKUs WAF.
- `WAF JS Challenge Request Count`: `generic_data`, métrica de Azure `WafJsChallengeRequestCount`, agregación Total. SKUs WAF.
- `WAF Penalty Box Hits`: `generic_data`, métrica de Azure `WafPenaltyBoxHits`, agregación Average. SKUs WAF.
- `WAF Penalty Box Size`: `generic_data`, métrica de Azure `WafPenaltyBoxSize`, agregación Average. SKUs WAF.
- `WAF Captcha Challenge Request Count`: `generic_data`, métrica de Azure `WafCaptchaChallengeRequestCount`, agregación Total. SKUs WAF.

**Módulos WebSocket**

- `WebSocket Active Connections`: `generic_data`, métrica de Azure `WebSocketActiveConnections`, agregación Average.
- `WebSocket Specific Close Status Code`: `generic_data`, métrica de Azure `WebSocketSpecificCloseStatusCode`, agregación Total.

**Módulo de recuento de Application Gateways**

- `Application Gateway Count`: `generic_data`, métrica de Azure `ApplicationGatewayCount`, agregación Total.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.azure.gateway` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |
