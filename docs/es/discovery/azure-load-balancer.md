# Azure Load Balancer Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de Azure Load Balancer descubre los Azure Load Balancers de una suscripción de Microsoft Azure y convierte su estado y sus métricas de Azure Monitor en agentes y módulos de Pandora FMS: disponibilidad de la ruta de datos, estado de las sondas de salud, tráfico de bytes, paquetes y SYN, puertos SNAT asignados y usados, conexiones SNAT, número de hosts del backend y un recuento por load balancer.

Por defecto crea **un agente por Load Balancer**, con el nombre del load balancer y un prefijo opcional. También puede consolidar todos los Load Balancers descubiertos en un único agente. Cada agente lleva un módulo de disponibilidad y un módulo por métrica habilitada.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.azure_load_balancer`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Microsoft Azure Network y Azure Monitor | `Requerido` | El plugin enumera los Load Balancers y lee sus métricas mediante estas API |
| Una entidad de servicio de Microsoft Entra capaz de listar Load Balancers y leer sus métricas de Azure Monitor | `Requerido` | El plugin lista los Load Balancers con el cliente de Network y lee las métricas con el cliente de Monitor. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure) |
| Un grupo de agentes de Pandora FMS con ID mayor que `0` | `Requerido` | El grupo `All` tiene ID `0` y no se puede usar |
| Nubes de Azure soberanas o personalizadas | `Sin validar` | Los endpoints son los públicos de Azure; ningún registro de pruebas establece su funcionamiento contra una nube no pública |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga Load Balancers.
3. **Una credencial de Azure** guardada en el almacén de credenciales de Pandora FMS, o sus valores suministrados directamente para una ejecución manual.
4. **Un grupo de agentes válido** para la tarea. El grupo `All` no es válido, porque su ID es `0`.

El plugin se distribuye como un ejecutable autocontenido: la aplicación Discovery empaquetada incluye `bin/pandora_azure_load_balancer`, por lo que no es necesario instalar ningún runtime adicional en el servidor de Pandora FMS ni para una ejecución manual.

### Preparar el acceso a Azure

Cree una entidad de servicio de Microsoft Entra que pueda enumerar los Load Balancers y leer sus métricas de Azure Monitor, sobre la suscripción o el Resource Group que se vaya a descubrir. El plugin lista los Load Balancers con el cliente de Azure Network y lee las métricas con el cliente de Azure Monitor, por lo que la entidad necesita acceso de lectura a ambos. No conceda un rol más amplio del que exige su política.

Guarde su **Account ID** (el client ID), **Application secret**, **Tenant or domain name** y **Subscription id** como una credencial de Azure en el almacén de credenciales de Pandora FMS, de modo que la tarea haga referencia a la credencial en lugar de transportar el secreto. El almacén de credenciales asigna estos cuatro valores al client ID, al secreto de aplicación, al tenant y a la suscripción de Azure.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Azure Load Balancer** aparece en la categoría **Cloud** del asistente de Discovery.

![Vista Cloud de Discovery con el plugin Azure Load Balancer instalado.](../assets/images/discovery/azure-load-balancer/cloud-menu.png)

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure Load Balancer**. El primer paso genérico del asistente define la tarea; el paquete añade **Azure Base**, **Azure Load Balancer Options** y **Metrics**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo, servidor e intervalo. El grupo debe tener un ID mayor que `0`; `All` no se puede usar. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure Base.** Qué suscripción leer y cuánto de ella:

- **Azure credentials** selecciona la credencial de Azure guardada. La credencial contiene el Account ID, el Application secret, el Tenant or domain name y el Subscription ID.
- **Custom Resource Group** limita el descubrimiento a un único Resource Group, y **Resource group** lo nombra exactamente. Aquí no se aceptan expresiones regulares.

<!-- SCREENSHOT NEEDED: Paso Azure Base del asistente con el selector de credencial, el conmutador Custom Resource Group y el campo Resource group. -->

**Paso 3 — Azure Load Balancer Options.** Distribución de agentes, caché de descubrimiento y diagnóstico:

- **Create one agent per Load Balancer** decide la distribución de agentes, y **Target agent** solo se usa cuando está deshabilitado.
- **Load Balancer agent prefix** nombra los agentes por load balancer.
- **Scan Load Balancers** consulta Azure para descubrir los Load Balancers actuales; cuando está deshabilitado se reutiliza el archivo de entidades en caché.
- **Enable entities file re-scan interval** y **Entities re-scan interval** controlan cuánto tiempo se reutiliza la caché antes de reconstruirse.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS.
- **Modules prefix** se antepone a todos los nombres de módulo generados.
- **Debug** revela las opciones de mock local, que existen solo para pruebas.

<!-- SCREENSHOT NEEDED: Paso Azure Load Balancer Options del asistente con los campos de distribución de agentes, caché y Debug. -->

**Paso 4 — Metrics.** Qué familias de métricas se recogen:

- **Max threads** procesa los Load Balancers descubiertos en paralelo.
- **Metrics time window** es el rango consultado en Azure Monitor, **Azure metric interval** es la granularidad temporal, **Metric timeout** acota cada petición y **Max retries** cubre los errores temporales de Azure y las respuestas HTTP 429.
- Un conmutador por familia de métricas: **Availability modules**, **Traffic modules**, **SNAT modules**, **Backend pool host count module** y **Load Balancer count module**.
- **Modules allow regexp** y **Modules deny regexp** filtran los nombres finales de los módulos.

<!-- SCREENSHOT NEEDED: Paso Metrics del asistente con los conmutadores de métricas, los campos de tiempo, intervalo, timeout y reintentos, y las expresiones regulares de allow y deny. -->

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de los agentes generados y de los objetivos activos e inactivos. Espere un agente por Load Balancer descubierto, o un único **Target agent** cuando la creación por load balancer está deshabilitada.

2. **Los agentes.** Nombrados `<Load Balancer agent prefix><nombre del load balancer>` por defecto, por lo que `Azure LB panda-frontend`. Cada uno informa de `Azure Load Balancer` como sistema operativo y hereda el grupo y el intervalo de la tarea.

3. **`connection`** es `1` en todo Load Balancer descubierto. Un `0` significa que el Load Balancer está en la caché pero ya no es descubrible — consulte [Solución de problemas](#solucion-de-problemas).

4. **Los módulos de métricas** de cada familia habilitada. El conjunto de módulos depende de los conmutadores: availability, traffic, SNAT, backend pool host count y load balancer count.

Si no aparece ningún agente, lo primero que hay que revisar son la credencial o sus permisos.

![Agentes gestionados creados por una tarea de Azure Load Balancer, uno por Load Balancer descubierto.](../assets/images/discovery/azure-load-balancer/managed-agents.png)

## Interpretar los resultados

### Distribución de agentes

**Con Create one agent per Load Balancer habilitado**, que es el valor por defecto, el plugin crea un agente por Load Balancer, llamado `<Load Balancer agent prefix><nombre del load balancer>`. Se inserta un separador cuando el prefijo no termina en espacio, guion, punto, guion bajo, barra o dos puntos, por lo que un prefijo de `Azure LB` se comporta como `Azure LB `.

**Con él deshabilitado**, todos los módulos van al único **Target agent** y el nombre del load balancer se antepone a cada nombre de módulo. Esto importa para el filtrado: las expresiones regulares allow y deny se evalúan contra el nombre *final* del módulo, que en modo consolidado incluye ese prefijo del load balancer.

Los agentes generados informan de `Azure Load Balancer` como sistema operativo, heredan el grupo y el intervalo de la tarea, y se crean en el modo `2` de Pandora FMS cuando **Agent autodisable mode** está habilitado, o en el modo `1` cuando está deshabilitado.

### Qué se crea

`connection` se crea siempre, como `generic_proc`, con valor `1` para un Load Balancer descubierto. Cuando un Load Balancer en caché deja de ser descubrible, su agente se conserva y este módulo informa de `0` hasta que la entidad se descarta en una reconstrucción de la caché.

El resto es `generic_data` o `generic_data_inc`, agrupado por la opción que lo habilita:

| Habilitado por | Qué se obtiene |
| --- | --- |
| Availability modules | `data path availability` y `health probe status` |
| Traffic modules | `byte count`, `packet count` y `SYN count` |
| SNAT modules | `allocated SNAT ports`, `used SNAT ports` y `SNAT connection count` |
| Backend pool host count module | `backend pool host count` |
| Load Balancer count module | `load balancer count` |

Los módulos `backend pool host count` y `load balancer count` los calcula el plugin a partir de la configuración de los backend pools del Load Balancer y del número de recursos descubiertos; el resto de módulos se leen de Azure Monitor. El inventario exhaustivo de módulos, tipos y unidades está en [Módulos generados](#modulos-generados).

## Solución de problemas

- **La tarea falla por el grupo** — el grupo de agentes debe tener un ID mayor que `0`. `All` es el grupo `0` y no se puede usar.
- **No se descubre ningún Load Balancer** — compruebe la entidad de servicio en este orden: los valores de la credencial (Account ID, Application secret, Tenant or domain, Subscription id), después que pueda listar los Load Balancers y leer sus métricas, y después si **Custom Resource Group** está limitando la búsqueda.
- **Un agente sobrevive con `connection` a `0`** — el Load Balancer está en la caché de entidades pero ya no es descubrible, porque se eliminó, se renombró o salió del ámbito configurado. El agente se conserva hasta que la caché se reconstruye, lo que ocurre tras **Entities re-scan interval**.
- **Faltan módulos esperados** — las expresiones regulares allow y deny se evalúan contra el nombre final del módulo. En modo consolidado ese nombre lleva el nombre del load balancer, por lo que una expresión escrita para el modo por load balancer no coincidirá.
- **Las peticiones agotan el tiempo o fallan con un estado HTTP reintentable** — suba **Metric timeout** o **Max retries**. El plugin reintenta los estados HTTP de Azure `408`, `429`, `500`, `502`, `503` y `504` hasta **Max retries** veces, respetando la cabecera `Retry-After` cuando está presente.
- **Debug, Mock Azure API URL** existen para apuntar el plugin a un mock local durante las pruebas. Deje **Debug** desactivado en entornos reales.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Azure Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Azure credentials | `_credentials_` | select | — | Credencial de Azure del almacén de credenciales de Pandora FMS. Obligatorio |
| Custom Resource Group | `_customResourceGroup_` | checkbox | off | Limita el descubrimiento a un Resource Group |
| Resource group | `_resourceGroup_` | string | — | Nombre exacto del Resource Group. Solo se muestra cuando la opción anterior está habilitada; no es una expresión regular |

#### Azure Load Balancer Options

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Target agent | `_engineAgent_` | string | `Azure Load Balancer` | Agente usado en modo consolidado. Solo se usa cuando **Create one agent per Load Balancer** está deshabilitado |
| Create one agent per Load Balancer | `_agentPerLoadBalancer_` | checkbox | on | Deshabilitado envía todos los módulos a **Target agent** |
| Load Balancer agent prefix | `_prefixAgent_` | string | `Azure LB ` | Prefijo de los agentes por load balancer. Solo se muestra cuando **Create one agent per Load Balancer** está habilitado |
| Agent autodisable mode | `_agentAutodisable_` | checkbox | off | Crea los agentes en el modo `2` cuando está habilitado, en el modo `1` en caso contrario |
| Modules prefix | `_prefixModuleName_` | string | — | Prefijo antepuesto a todos los nombres de módulo generados |
| Scan Load Balancers | `_scanLoadBalancers_` | checkbox | on | Consulta Azure para descubrir los Load Balancers actuales |
| Enable entities file re-scan interval | `_enableEntitiesInterval_` | checkbox | off | Reutiliza la caché descubierta hasta que el intervalo expira |
| Entities re-scan interval | `_entitiesInterval_` | select | `86400` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Debug | `_debugMode_` | checkbox | off | Revela las opciones de mock local, que existen solo para pruebas |
| Mock Azure API URL | `_mockApiUrl_` | string | — | URL base del mock local. Solo se muestra cuando **Debug** está habilitado; déjelo vacío en entornos reales |

#### Metrics

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `1` | Trabajadores en paralelo que procesan los Load Balancers descubiertos |
| Metrics time window | `_timeWindow_` | select | `300` | Rango consultado en Azure Monitor para cada petición, en segundos |
| Azure metric interval | `_metricInterval_` | select | `PT5M` | Granularidad temporal de Azure Monitor (`PT1M`, `PT5M`, `PT15M`, `PT30M`, `PT1H`, `PT6H`, `PT12H`, `P1D`) |
| Metric timeout | `_metricTimeout_` | number | `30` | Tiempo de espera de la petición en segundos; `0` o negativo usa `30` |
| Max retries | `_maxRetries_` | number | `3` | Reintentos para errores temporales de Azure y respuestas HTTP 429 |
| Availability modules | `_checkAvailabilityModules_` | checkbox | on | `data path availability` y `health probe status` |
| Traffic modules | `_checkTrafficModules_` | checkbox | on | `byte count`, `packet count` y `SYN count` |
| SNAT modules | `_checkSnatModules_` | checkbox | on | `allocated SNAT ports`, `used SNAT ports` y `SNAT connection count` |
| Backend pool host count module | `_checkBackendPoolHostCount_` | checkbox | on | `backend pool host count` |
| Load Balancer count module | `_checkLoadBalancerCount_` | checkbox | on | `load balancer count` |
| Modules allow regexp | `_moduleallowlist_` | textarea | — | Una expresión por línea. Solo se conservan los nombres de módulo que coinciden con al menos una |
| Modules deny regexp | `_moduledenylist_` | textarea | — | Una expresión por línea. Los nombres de módulo coincidentes se excluyen. Deny tiene prioridad sobre allow |

### Claves del archivo de configuración

La tarea de Discovery construye este archivo a partir de sus propios campos; una ejecución manual lo suministra con `--conf`. Las listas allow y deny se pasan como rutas de archivo con `--module_allow_list_file` y `--module_deny_list_file`, una expresión por línea.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `agents_group_id` | ID de grupo de Pandora FMS asignado a los agentes generados. Debe ser mayor que `0` | Obligatorio |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` en ejecuciones manuales |
| `credentials` | Credencial de Azure codificada en base64 generada por Pandora FMS | Vacío |
| `subscription_id`, `tenant_id`, `client_id`, `client_secret` | Valores de credencial manuales, usados cuando no se proporciona `credentials` | Vacío |
| `resource_group` | Limita el descubrimiento a un Resource Group exacto | Vacío |
| `target_agent` | Agente usado en modo consolidado | `Azure Load Balancer` |
| `modules_prefix` | Prefijo de todos los nombres de módulo generados | Vacío |
| `scan_load_balancers` | Consulta Azure para descubrir los Load Balancers | `1` |
| `agent_per_load_balancer` | Crea un agente por Load Balancer cuando está habilitado | `1` |
| `lb_agent_prefix` | Prefijo de los agentes por load balancer | `Azure LB ` |
| `agent_autodisable` | Usa el modo `2` de Pandora FMS cuando está habilitado y el modo `1` en caso contrario | `0` |
| `entities_list` | Ruta de la caché de entidades de Load Balancer | Vacío en ejecuciones manuales |
| `enable_entities_interval` | Conserva las entidades en caché hasta que el intervalo configurado expira | `1` |
| `entities_interval` | Intervalo de reconstrucción de la caché de entidades en segundos | `86400` |
| `time_window` | Rango consultado en Azure Monitor, en segundos | `300` |
| `metric_interval` | Granularidad temporal de Azure Monitor | `PT5M` |
| `metric_timeout` | Tiempo de espera de la petición a Azure en segundos | `30` |
| `max_retries` | Reintentos para errores de Azure reintentables y HTTP 429 | `3` |
| `check_availability_modules` | Habilita los módulos de disponibilidad | `1` |
| `check_traffic_modules` | Habilita los módulos de tráfico | `1` |
| `check_snat_modules` | Habilita los módulos SNAT | `1` |
| `check_backend_pool_host_count` | Habilita el módulo de número de hosts del backend | `1` |
| `check_load_balancer_count` | Habilita el módulo de recuento de load balancers | `1` |
| `debug` | Habilita las opciones de mock local. Solo para pruebas | `0` |
| `mock_api_url` | URL base del mock local. Solo para pruebas | Vacío |

El plugin reintenta los estados HTTP de Azure `408`, `429`, `500`, `502`, `503` y `504` hasta **Max retries** veces, respetando la cabecera `Retry-After` cuando está presente; el número de reintentos es configurable mediante **Max retries**.

### Ejecución en línea de comandos

El plugin lee un único archivo de configuración. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de tarea.

```bash
./pandora_azure_load_balancer --conf <PATH_TO_CONFIG>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta obligatoria al archivo de configuración |
| `--module_allow_list_file` | Ruta opcional al archivo de expresiones regulares allow de módulos |
| `--module_deny_list_file` | Ruta opcional al archivo de expresiones regulares deny de módulos |

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

Cada módulo lleva el prefijo del nombre del load balancer cuando **Create one agent per Load Balancer** está deshabilitado, y el **Modules prefix** cuando está definido.

**Siempre se crea**

- `connection`: `generic_proc`, `1` para un Load Balancer descubierto.

**Módulos de disponibilidad**

- `data path availability`: `generic_data`, disponibilidad media de la ruta de datos; unidad `%`.
- `health probe status`: `generic_data`, estado medio de la sonda de salud; unidad `%`.

**Módulos de tráfico**

- `byte count`: `generic_data_inc`, total de bytes transmitidos; unidad `bytes`.
- `packet count`: `generic_data_inc`, total de paquetes transmitidos; unidad `packets`.
- `SYN count`: `generic_data_inc`, total de paquetes SYN transmitidos; unidad `packets`.

**Módulos SNAT**

- `allocated SNAT ports`: `generic_data`, número de puertos SNAT asignados; unidad `ports`.
- `used SNAT ports`: `generic_data`, número de puertos SNAT usados; unidad `ports`.
- `SNAT connection count`: `generic_data_inc`, nuevas conexiones SNAT creadas; unidad `connections`.

**Módulo de número de hosts del backend**

- `backend pool host count`: `generic_data`, número de hosts del backend configurados en los backend pools del load balancer; unidad `hosts`. Lo calcula el plugin a partir de la configuración de los backend pools del Load Balancer.

**Módulo de recuento de load balancers**

- `load balancer count`: `generic_data`, recuento de recursos de Azure Load Balancer descubiertos; unidad `count`. Lo calcula el plugin, uno por Load Balancer descubierto.

Las vistas de módulos de la consola para cada familia:

![Módulos de disponibilidad en un agente de Azure Load Balancer.](../assets/images/discovery/azure-load-balancer/availability-modules.png)

![Módulos de tráfico en un agente de Azure Load Balancer.](../assets/images/discovery/azure-load-balancer/traffic-modules.png)

![Módulos SNAT en un agente de Azure Load Balancer.](../assets/images/discovery/azure-load-balancer/snat-modules.png)

![Módulo de número de hosts del backend en un agente de Azure Load Balancer.](../assets/images/discovery/azure-load-balancer/backend-pool-count.png)

![Módulo de recuento de load balancers en un agente de Azure Load Balancer.](../assets/images/discovery/azure-load-balancer/load-balancer-count.png)

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.azure_load_balancer` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |