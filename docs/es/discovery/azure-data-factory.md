# Azure Data Factory Discovery

*Última actualización del artículo: 2026-11-10.*

## Qué monitoriza

El plugin de Discovery de Azure Data Factory recupera las Data Factories de una suscripción de Microsoft Azure y convierte sus métricas de Azure Monitor en agentes y módulos de Pandora FMS: ejecuciones de pipeline, actividad y trigger, capacidad y límites de entidades de la factoría, salud del integration runtime, actividad de SSIS, actividad del integration runtime de Airflow y capacidad de la red virtual administrada.

Por defecto crea **un agente por Data Factory**, con el nombre de la Data Factory y un prefijo opcional. También puede consolidar todas las Data Factories recuperadas en un único agente. Cada agente lleva un módulo de conexión, un recuento de Data Factories y un módulo por cada métrica habilitada que Azure Monitor devuelve para el recurso.

Una extensión de consola complementaria, **Azure Data Factory Dashboard**, presenta los agentes y módulos generados en una vista consolidada con contadores de ejecución, gráficas históricas, paneles de integration runtime y capacidad, resúmenes de estado y una tabla por Data Factory.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.azure.datafactory`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Microsoft Azure Data Factory, Azure Resource Manager y Azure Monitor | `Requerido` | El plugin lista las Data Factories con la API de Azure Resource Manager y lee sus métricas con la API de Azure Monitor |
| Una entidad de servicio de Microsoft Entra capaz de listar Data Factories y leer sus métricas de Azure Monitor | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure) |
| Un grupo de agentes de Pandora FMS con ID mayor que `0` | `Requerido` | El grupo `All` tiene ID `0` y no se puede usar |
| Nubes de Azure soberanas o personalizadas | `Sin validar` | Los endpoints son los públicos de Azure; ningún registro de pruebas establece su funcionamiento contra una nube no pública |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga Data Factories.
3. **Una credencial de Azure** guardada en el almacén de credenciales de Pandora FMS, o sus valores suministrados directamente para una ejecución manual.
4. **Un grupo de agentes válido** para la tarea. El grupo `All` no es válido, porque su ID es `0`.

El plugin se distribuye como un ejecutable autocontenido: la aplicación Discovery empaquetada incluye `bin/pandora_azure_datafactory`, por lo que no es necesario instalar ningún runtime adicional en el servidor de Pandora FMS ni para una ejecución manual.

### Preparar el acceso a Azure

Cree una entidad de servicio de Microsoft Entra que pueda listar las Data Factories y leer sus métricas de Azure Monitor, sobre la suscripción o el Resource Group que se vaya a descubrir. El plugin lista las Data Factories con la API de Azure Resource Manager y lee las métricas con la API de Azure Monitor, por lo que la entidad necesita acceso de lectura a ambas. No conceda un rol más amplio del que exige su política.

Guarde su **Client ID**, **Application secret**, **Tenant or domain name** y **Subscription id** como una credencial de Azure en el almacén de credenciales de Pandora FMS, de modo que la tarea haga referencia a la credencial en lugar de transportar el secreto.

En la mayoría de entornos basta con un rol que tenga acceso de lectura sobre la suscripción o el Resource Group. Por ejemplo, el rol integrado `Reader` puede listar las Data Factories y leer sus métricas; use el ámbito más restrictivo que permita su política. La entidad se crea desde la CLI de Azure con:

```bash
az ad sp create-for-rbac \
  --name pandora-azure-data-factory-discovery \
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

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Azure Data Factory** aparece en la categoría **Cloud** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure Data Factory**. El primer paso genérico del asistente define la tarea; el paquete añade **Azure Base**, **Data Factory Options** y **Metrics**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo, servidor e intervalo. El grupo debe tener un ID mayor que `0`; `All` no se puede usar. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure Base.** Qué suscripción leer y cuánto de ella:

- **Azure credentials** selecciona la credencial de Azure guardada. La credencial contiene el Client ID, el Application secret, el Tenant or domain name y el Subscription ID.
- **Custom Resource Group** limita el descubrimiento a un único Resource Group, y **Resource group** lo nombra exactamente. Aquí no se aceptan expresiones regulares.

![Paso Azure Base del asistente con el selector de credencial y el conmutador Custom Resource Group. La credencial mostrada es de prueba; seleccione la credencial de Azure creada para su entorno.](../assets/images/discovery/azure-data-factory/azure-base.png)

**Paso 3 — Data Factory Options.** Distribución de agentes, caché de descubrimiento y diagnóstico:

- **Target agent** solo se usa cuando **Create one agent per Data Factory** está deshabilitado.
- **Scan Data Factories** consulta Azure para recuperar las Data Factories actuales; cuando está deshabilitado se reutiliza el archivo de entidades en caché.
- **Create one agent per Data Factory** decide la distribución de agentes: un agente por recurso, o todos los módulos en el único **Target agent**.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS.
- **Data Factory agent prefix** nombra los agentes por Data Factory.
- **Modules prefix** se antepone a todos los nombres de módulo generados.
- **Enable entities file re-scan interval** y **Entities re-scan interval** controlan cuánto tiempo se reutiliza la caché recuperada antes de reconstruirse.
- **Debug** revela la opción de mock local, que existe solo para pruebas. Deje **Debug** desactivado y **Mock Azure API URL** vacío en entornos reales.

![Paso Data Factory Options del asistente con los campos de distribución de agentes, caché y Debug. La captura usa un mock local; en producción deje Debug desactivado y Mock Azure API URL vacío.](../assets/images/discovery/azure-data-factory/datafactory-options.png)

**Paso 4 — Metrics.** Qué familias de métricas se recogen:

- **Metrics time window** es el rango consultado en Azure Monitor y **Azure metric interval** es la granularidad temporal.
- **Metric timeout** acota cada petición y **Max retries** cubre los errores temporales de Azure y las respuestas HTTP 429.
- Un conmutador por familia de métricas: **Pipeline run modules**, **Activity run modules**, **Trigger run modules**, **Factory capacity modules**, **Integration runtime modules**, **SSIS modules**, **Airflow modules**, **Managed VNet modules** y **Data Factory count module**.
- **Modules allow regexp** y **Modules deny regexp** filtran los nombres finales de los módulos.

![Paso Metrics del asistente con los conmutadores de familias de métricas, los campos de tiempo, intervalo, timeout y reintentos, y las expresiones regulares de allow y deny.](../assets/images/discovery/azure-data-factory/metrics.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de `data_factories_discovered`, `data_factories_vanished`, `modules`, `errors`, `unsupported_metrics` y `scan_source`. `scan_source` es `azure` cuando la ejecución recuperó las Data Factories desde Azure, o `entities_cache` cuando se reutilizó la caché de entidades.

2. **Los agentes.** Nombrados `<Data Factory agent prefix><nombre de la Data Factory>` por defecto, por lo que `Azure Data Factory adf-prod`. Cada uno informa de `Azure` como sistema operativo y de `Azure Data Factory` como versión, y hereda el grupo y el intervalo de la tarea. La dirección del agente es el nombre de la Data Factory y su descripción es el ID del recurso de Azure.

3. **`Data Factory Connection`** es `1` en toda Data Factory recuperada. Un `0` significa que la Data Factory está en la caché pero ya no es recuperable — consulte [Solución de problemas](#solucion-de-problemas).

4. **`Data Factory Count`** es `1` en cada agente por Data Factory. En modo consolidado informa del número de Data Factories recuperadas en la ejecución.

5. **Los módulos de métricas** de cada familia habilitada, para aquellas métricas que Azure Monitor realmente informa del recurso.

![Resumen de la tarea tras una ejecución correcta, con las Data Factories descubiertas, el número de módulos, los errores y las métricas no soportadas.](../assets/images/discovery/azure-data-factory/task-summary.png)

![Agentes gestionados creados por una tarea de Azure Data Factory, uno por Data Factory recuperada.](../assets/images/discovery/azure-data-factory/managed-agents.png)

Si no aparece ningún agente, lo primero que hay que revisar son la credencial o sus permisos.

## Interpretar los resultados

### Distribución de agentes

**Con Create one agent per Data Factory habilitado**, que es el valor por defecto, el plugin crea un agente por Data Factory, llamado `<Data Factory agent prefix><nombre de la Data Factory>`. Se inserta un separador cuando el prefijo no termina en espacio, guion o guion bajo, por lo que un prefijo de `Azure Data Factory` se comporta como `Azure Data Factory `.

**Con él deshabilitado**, todos los módulos van al único **Target agent** y el nombre de la Data Factory se antepone a cada nombre de módulo. Esto importa para el filtrado: las expresiones regulares allow y deny se evalúan contra el nombre *final* del módulo, que en modo consolidado incluye ese prefijo de la Data Factory.

Los agentes generados informan de `Azure` como sistema operativo, heredan el grupo y el intervalo de la tarea, y se crean en el modo `2` de Pandora FMS cuando **Agent autodisable mode** está habilitado, o en el modo `1` cuando está deshabilitado. La dirección del agente es el nombre de la Data Factory y su descripción es el ID del recurso de Azure.

### Caché de descubrimiento y recursos desaparecidos

El plugin mantiene una caché de entidades ligada a la tarea en `entities_list`, sembrada desde la API de Data Factory y reutilizada entre ejecuciones. La caché está acotada por tarea, de modo que dos tareas configuradas sobre la misma suscripción no comparten sus entidades recuperadas.

`Data Factory Connection` se crea siempre, como `generic_proc`, con valor `1` para una Data Factory recuperada. Cuando una Data Factory en caché deja de ser recuperable, su agente se conserva y este módulo informa de `0` hasta que la entidad se descarta en una reconstrucción de la caché.

### Qué se crea

`Data Factory Connection` es el único módulo `generic_proc`; su descripción registra si el recurso se encontró en el descubrimiento actual. `Data Factory Count` es un módulo `generic_data` local que cuenta las Data Factories representadas por el agente. Todas las métricas de Azure son módulos `generic_data` y se agrupan por la opción que las habilita:

| Habilitado por | Qué se obtiene |
| --- | --- |
| Pipeline run modules | `Pipeline Cancelled Runs`, `Pipeline Elapsed Time Runs`, `Pipeline Failed Runs` y `Pipeline Succeeded Runs` |
| Activity run modules | `Activity Cancelled Runs`, `Activity Failed Runs` y `Activity Succeeded Runs` |
| Trigger run modules | `Trigger Cancelled Runs`, `Trigger Failed Runs` y `Trigger Succeeded Runs` |
| Factory capacity modules | `Factory Size (GB)`, `Max Allowed Factory Size (GB)`, `Resource Count` y `Max Allowed Resource Count` |
| Integration runtime modules | `Integration Runtime Available Memory`, `Integration Runtime Available Nodes`, `Integration Runtime Average Task Pickup Delay`, `Integration Runtime CPU Percentage` y `Integration Runtime Queue Length` |
| SSIS modules | Contadores de inicio y parada del integration runtime de SSIS y de ejecución de paquetes SSIS |
| Airflow modules | Contadores de salud, procesamiento de DAG, executor, scheduler, pool, instancias de tarea y triggers del integration runtime de Airflow |
| Managed VNet modules | Utilización y colas de espera de copia, externas y de pipeline de la red virtual administrada |
| Data Factory count module | `Data Factory Count` |

Todos los módulos de métricas de Azure llevan la descripción `Azure metric <MetricName> (<Aggregation>)`. El plugin pregunta a Azure Monitor qué métricas hay disponibles para el recurso y descarta el resto. Una métrica que Azure rechaza se reintenta por separado y, si sigue fallando, se cuenta en `unsupported_metrics` en lugar de abortar la ejecución. El inventario exhaustivo de módulos está en [Módulos generados](#modulos-generados).

Las métricas de ejecución se recogen a nivel de Data Factory. El plugin no crea agentes ni módulos separados por pipeline, actividad o trigger, ni entidades por integration runtime. Las métricas de Airflow y de red virtual administrada solo generan módulos cuando Azure Monitor devuelve datos para ellas; las factorías que no usan esos integration runtimes simplemente no generan esos módulos.

![Módulos creados en un agente de Azure Data Factory, con el nombre de la métrica de Azure y la agregación en cada descripción.](../assets/images/discovery/azure-data-factory/agent-modules.png)

### Panel complementario

La extensión de consola **Azure Data Factory Dashboard** es un paquete separado que presenta los datos generados por este plugin. Instálela desde el gestor de extensiones de Pandora FMS; una vez instalada, aparece en **Monitoring → Azure Data Factory Dashboard**.

El panel lee los agentes y módulos creados por la tarea de Discovery. Ofrece un filtro por Data Factory y un periodo histórico y muestra:

- Indicadores de ejecuciones de pipeline, actividad y trigger con tasas de éxito y fallo.
- Recuentos de entidades y límites de capacidad de las Data Factories.
- Gráficas históricas de ejecuciones de pipeline, actividad y trigger y de CPU y longitud de cola del integration runtime.
- Resúmenes de integration runtime y capacidad de la factoría.
- Paneles de SSIS, Airflow y red virtual administrada cuando las métricas correspondientes tienen datos.
- Resúmenes de estado de agentes y módulos y una tabla por Data Factory.

La extensión identifica los datos del plugin por los metadatos de descubrimiento almacenados en los agentes y módulos generados y, si no están disponibles, recurre a sus nombres. Muestra un estado vacío controlado hasta que la primera ejecución de Discovery crea datos. No necesita credenciales adicionales de Azure; lee los valores que Pandora FMS ya ha almacenado.

![Azure Data Factory Dashboard con los indicadores de pipeline, actividad, trigger y entidades y las gráficas históricas de ejecución.](../assets/images/discovery/azure-data-factory/dashboard-overview.png)

![Azure Data Factory Dashboard con el historial de trigger e integration runtime, los paneles de integration runtime y capacidad y los resúmenes de SSIS y Airflow.](../assets/images/discovery/azure-data-factory/dashboard-runtime.png)

![Azure Data Factory Dashboard con el panel de red virtual administrada, los resúmenes de estado de agentes y módulos y la tabla por Data Factory.](../assets/images/discovery/azure-data-factory/dashboard-status.png)

## Solución de problemas

- **La tarea falla por el grupo** — el grupo de agentes debe tener un ID mayor que `0`. `All` es el grupo `0` y no se puede usar.
- **No se recupera ninguna Data Factory** — compruebe la entidad de servicio en este orden: los valores de la credencial, después que pueda listar las Data Factories y leer sus métricas, y después si **Custom Resource Group** está limitando la búsqueda.
- **`Missing Azure credential values`** — no se ha resuelto ninguna credencial de Azure utilizable. Seleccione una credencial de Azure válida en **Azure Base** o, para una ejecución manual, proporcione `credentials` o las claves `tenant_id`, `client_id` y `client_secret`.
- **`subscription_id is required`** — la credencial seleccionada no contiene un Subscription ID. Guárdelo en la credencial de Azure o proporcione `subscription_id` para una ejecución manual.
- **Un agente sobrevive con `Data Factory Connection` a `0`** — la Data Factory está en la caché de entidades pero ya no es recuperable, porque se eliminó, se renombró o salió del ámbito configurado. El agente se conserva hasta que la caché se reconstruye, lo que ocurre tras **Entities re-scan interval**.
- **Faltan módulos esperados** — las expresiones regulares allow y deny se evalúan contra el nombre final del módulo. En modo consolidado ese nombre lleva el nombre de la Data Factory, por lo que una expresión escrita para el modo por Data Factory no coincidirá. Las métricas de Airflow y de red virtual administrada que Azure Monitor no informa del recurso también se descartan y se cuentan en `unsupported_metrics`.
- **Azure rechaza una petición de métricas con HTTP 400 `Failed to find metric configuration`** — una métrica del lote no es válida para esa Data Factory. El plugin reintenta las métricas individualmente y descarta la no soportada, de modo que la ejecución termina bien; consulte `unsupported_metrics` para ver la lista.
- **Las peticiones agotan el tiempo o fallan con un estado HTTP reintentable** — suba **Metric timeout** o **Max retries**. El plugin reintenta los estados HTTP de Azure 429, 500, 502, 503 y 504 hasta **Max retries** veces, respetando la cabecera `Retry-After` cuando está presente.
- **`scan_source` informa `entities_cache`** — la caché de entidades sigue vigente, por lo que la ejecución reutilizó las Data Factories recuperadas anteriormente en lugar de consultar Azure. Aumente la frecuencia de reconstrucción de la caché o límpiela si necesita un reescaneo inmediato.
- **El panel está vacío aunque existan agentes** — compruebe que la extensión Azure Data Factory Dashboard está instalada y que los agentes pertenecen a la tarea de Azure Data Factory. La extensión muestra un estado vacío hasta que los agentes y módulos generados contienen datos.
- **Debug y Mock Azure API URL** existen para apuntar el plugin a un mock local durante las pruebas. Deje **Debug** desactivado y **Mock Azure API URL** vacío en entornos reales.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Azure Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Azure credentials | `_credentials_` | select | — | Credencial de Azure del almacén de credenciales de Pandora FMS. Obligatorio |
| Custom Resource Group | `_customresourcegroup_` | checkbox | off | Limita el descubrimiento a un Resource Group |
| Resource group | `_resourcegroup_` | string | — | Nombre exacto del Resource Group. Solo se muestra cuando la opción anterior está habilitada; no es una expresión regular |

#### Data Factory Options

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Target agent | `_targetagent_` | string | `Azure Data Factories` | Agente usado en modo consolidado. Solo se usa cuando **Create one agent per Data Factory** está deshabilitado |
| Scan Data Factories | `_scanfactories_` | checkbox | on | Consulta Azure para recuperar las Data Factories actuales |
| Create one agent per Data Factory | `_agentperfactory_` | checkbox | on | Deshabilitado envía todos los módulos a **Target agent** |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` cuando está habilitado, en el modo `1` en caso contrario |
| Data Factory agent prefix | `_factoryagentprefix_` | string | `Azure Data Factory ` | Prefijo de los agentes por Data Factory |
| Modules prefix | `_modulesprefix_` | string | — | Prefijo antepuesto a todos los nombres de módulo generados |
| Enable entities file re-scan interval | `_enableentitiesinterval_` | checkbox | on | Reutiliza la caché recuperada hasta que el intervalo expira |
| Entities re-scan interval | `_entitiesinterval_` | select | `3600` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Debug | `_debug_` | checkbox | off | Revela la opción de mock local, que existe solo para pruebas |
| Mock Azure API URL | `_mockapiurl_` | string | — | URL base del mock local. Solo se muestra cuando **Debug** está habilitado; déjela vacía en entornos reales |

#### Metrics

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Metrics time window | `_timewindow_` | select | `300` | Rango consultado en Azure Monitor para cada petición, en segundos |
| Azure metric interval | `_metricinterval_` | select | `PT5M` | Granularidad temporal de Azure Monitor (`PT1M`, `PT5M`, `PT15M`, `PT30M`, `PT1H`, `PT6H`, `PT12H`, `P1D`) |
| Metric timeout | `_metrictimeout_` | number | `30` | Tiempo de espera de la petición en segundos; `0` o negativo usa `30` |
| Max retries | `_maxretries_` | number | `2` | Reintentos para errores temporales de Azure y respuestas HTTP 429 |
| Pipeline run modules | `_checkpipeline_` | checkbox | on | Ejecuciones de pipeline canceladas, con tiempo transcurrido, fallidas y correctas |
| Activity run modules | `_checkactivity_` | checkbox | on | Ejecuciones de actividad canceladas, fallidas y correctas |
| Trigger run modules | `_checktrigger_` | checkbox | on | Ejecuciones de trigger canceladas, fallidas y correctas |
| Factory capacity modules | `_checkfactory_` | checkbox | on | Tamaño de la factoría, tamaño máximo permitido, recuento de recursos y recuento máximo permitido |
| Integration runtime modules | `_checkintegrationruntime_` | checkbox | on | Memoria, nodos, retardo de recogida, CPU y longitud de cola del integration runtime |
| SSIS modules | `_checkssis_` | checkbox | on | Contadores de inicio y parada del integration runtime de SSIS y de ejecución de paquetes SSIS |
| Airflow modules | `_checkairflow_` | checkbox | on | Contadores de salud, procesamiento de DAG, executor, scheduler, pool, instancias de tarea y triggers del integration runtime de Airflow |
| Managed VNet modules | `_checkmvnet_` | checkbox | on | Utilización y colas de espera de copia, externas y de pipeline de la red virtual administrada |
| Data Factory count module | `_checkcount_` | checkbox | on | `Data Factory Count` |
| Modules allow regexp | `_moduleallowlist_` | textarea | — | Una expresión por línea. Solo se conservan los nombres de módulo que coinciden con al menos una |
| Modules deny regexp | `_moduledenylist_` | textarea | — | Una expresión por línea. Los nombres de módulo coincidentes se excluyen. Deny tiene prioridad sobre allow |

### Claves del archivo de configuración

La tarea de Discovery construye este archivo a partir de sus propios campos; una ejecución manual lo suministra con `--conf`. Las listas allow y deny se pasan como rutas de archivo con las claves `module_allow_list_file` y `module_deny_list_file`, una expresión por línea.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `agents_group_id` | ID de grupo de Pandora FMS asignado a los agentes generados. Debe ser mayor que `0` | Obligatorio |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` en ejecuciones manuales |
| `credentials` | Credencial de Azure codificada en base64 generada por Pandora FMS | Vacío |
| `subscription_id`, `tenant_id`, `client_id`, `client_secret` | Valores de credencial manual, usados cuando no se proporciona `credentials` | Vacío |
| `resource_group` | Limita el descubrimiento a un Resource Group exacto | Vacío |
| `target_agent` | Agente usado en modo consolidado | `Azure Data Factories` |
| `agent_per_data_factory` | Crea un agente por Data Factory cuando está habilitado | `1` |
| `agent_autodisable` | Usa el modo `2` de Pandora FMS cuando está habilitado y el modo `1` en caso contrario | `0` |
| `data_factory_agent_prefix` | Prefijo de los agentes por Data Factory | `Azure Data Factory ` |
| `modules_prefix` | Prefijo de todos los nombres de módulo generados | Vacío |
| `scan_data_factories` | Consulta Azure para recuperar las Data Factories | `1` |
| `entities_list` | Ruta de la caché de entidades de Data Factory | Vacío en ejecuciones manuales |
| `task_md5` | Identificador de tarea usado para acotar la caché de entidades a esta tarea | Vacío en ejecuciones manuales |
| `enable_entities_interval` | Conserva las entidades en caché hasta que expira el intervalo configurado | `1` |
| `entities_interval` | Intervalo de reconstrucción de la caché de entidades en segundos | `3600` |
| `time_window` | Rango consultado en Azure Monitor, en segundos | `300` |
| `metric_interval` | Granularidad temporal de Azure Monitor | `PT5M` |
| `metric_timeout` | Tiempo de espera de las peticiones a Azure en segundos | `30` |
| `max_retries` | Reintentos para errores reintentables de Azure y HTTP 429 | `2` |
| `output_format` | Formato de salida, `json` o `xml` | `json` |
| `module_allow_list` / `module_allow_list_file` | Expresiones regulares de allow en línea o en archivo | Vacío |
| `module_deny_list` / `module_deny_list_file` | Expresiones regulares de deny en línea o en archivo | Vacío |
| `check_pipeline_modules` | Habilita los módulos de ejecuciones de pipeline | `1` |
| `check_activity_modules` | Habilita los módulos de ejecuciones de actividad | `1` |
| `check_trigger_modules` | Habilita los módulos de ejecuciones de trigger | `1` |
| `check_factory_modules` | Habilita los módulos de capacidad de la factoría | `1` |
| `check_integration_runtime_modules` | Habilita los módulos de integration runtime | `1` |
| `check_ssis_modules` | Habilita los módulos de SSIS | `1` |
| `check_airflow_modules` | Habilita los módulos de Airflow | `1` |
| `check_mvnet_modules` | Habilita los módulos de red virtual administrada | `1` |
| `check_count_module` | Habilita el módulo de recuento de Data Factories | `1` |
| `mock_api_url` | URL base del mock local. Solo para pruebas | Vacío |

### Ejecución desde la línea de comandos

El plugin lee un único archivo de configuración. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de la tarea.

```bash
./pandora_azure_datafactory --conf <PATH_TO_CONFIG>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta obligatoria al archivo de configuración |
| `--version` | Muestra la versión del plugin y termina |

Archivo de configuración mínimo para una ejecución manual:

```ini
[CONF]
subscription_id=<SUBSCRIPTION_ID>
tenant_id=<TENANT_ID>
client_id=<CLIENT_ID>
client_secret=<CLIENT_SECRET>
agents_group_id=<GROUP_ID>
```

Ese archivo contiene una credencial en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin, manténgalo fuera de directorios compartidos y del control de versiones, y prefiera el almacén de credenciales de Pandora FMS para las tareas, donde la tarea referencia la credencial en lugar de transportarla.

### Módulos generados

Todos los módulos siguientes llevan el prefijo del nombre de la Data Factory cuando **Create one agent per Data Factory** está deshabilitado, y el **Modules prefix** cuando está configurado.

#### Siempre creados

- `Data Factory Connection`: `generic_proc`, `1` para una Data Factory recuperada y `0` cuando ya no es recuperable. La descripción registra el estado del descubrimiento.
- `Data Factory Count`: `generic_data`, `1` por agente en modo por Data Factory o el número de Data Factories recuperadas en modo consolidado.

#### Módulos de ejecuciones de pipeline

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| Pipeline Cancelled Runs | `generic_data` | `PipelineCancelledRuns` | Total | - |
| Pipeline Elapsed Time Runs | `generic_data` | `PipelineElapsedTimeRuns` | Total | - |
| Pipeline Failed Runs | `generic_data` | `PipelineFailedRuns` | Total | - |
| Pipeline Succeeded Runs | `generic_data` | `PipelineSucceededRuns` | Total | - |

#### Módulos de ejecuciones de actividad

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| Activity Cancelled Runs | `generic_data` | `ActivityCancelledRuns` | Total | - |
| Activity Failed Runs | `generic_data` | `ActivityFailedRuns` | Total | - |
| Activity Succeeded Runs | `generic_data` | `ActivitySucceededRuns` | Total | - |

#### Módulos de ejecuciones de trigger

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| Trigger Cancelled Runs | `generic_data` | `TriggerCancelledRuns` | Total | - |
| Trigger Failed Runs | `generic_data` | `TriggerFailedRuns` | Total | - |
| Trigger Succeeded Runs | `generic_data` | `TriggerSucceededRuns` | Total | - |

#### Módulos de capacidad de la factoría

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| Factory Size (GB) | `generic_data` | `FactorySizeInGbUnits` | Maximum | GB |
| Max Allowed Factory Size (GB) | `generic_data` | `MaxAllowedFactorySizeInGbUnits` | Maximum | GB |
| Resource Count | `generic_data` | `ResourceCount` | Maximum | - |
| Max Allowed Resource Count | `generic_data` | `MaxAllowedResourceCount` | Maximum | - |

#### Módulos de integration runtime

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| Integration Runtime Available Memory | `generic_data` | `IntegrationRuntimeAvailableMemory` | Average | bytes |
| Integration Runtime Available Nodes | `generic_data` | `IntegrationRuntimeAvailableNodeNumber` | Average | - |
| Integration Runtime Average Task Pickup Delay | `generic_data` | `IntegrationRuntimeAverageTaskPickupDelay` | Average | s |
| Integration Runtime CPU Percentage | `generic_data` | `IntegrationRuntimeCpuPercentage` | Average | % |
| Integration Runtime Queue Length | `generic_data` | `IntegrationRuntimeQueueLength` | Average | - |

#### Módulos de SSIS

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| SSIS IR Start Cancelled | `generic_data` | `SSISIntegrationRuntimeStartCancel` | Total | - |
| SSIS IR Start Failed | `generic_data` | `SSISIntegrationRuntimeStartFailed` | Total | - |
| SSIS IR Start Succeeded | `generic_data` | `SSISIntegrationRuntimeStartSucceeded` | Total | - |
| SSIS IR Stop Stuck | `generic_data` | `SSISIntegrationRuntimeStopStuck` | Total | - |
| SSIS IR Stop Succeeded | `generic_data` | `SSISIntegrationRuntimeStopSucceeded` | Total | - |
| SSIS Package Execution Cancelled | `generic_data` | `SSISPackageExecutionCancel` | Total | - |
| SSIS Package Execution Failed | `generic_data` | `SSISPackageExecutionFailed` | Total | - |
| SSIS Package Execution Succeeded | `generic_data` | `SSISPackageExecutionSucceeded` | Total | - |

#### Módulos de Airflow

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| Airflow IR Celery Task Timeout Error | `generic_data` | `AirflowIntegrationRuntimeCeleryTaskTimeoutError` | Total | - |
| Airflow IR Collect DB Dags | `generic_data` | `AirflowIntegrationRuntimeCollectDBDags` | Average | ms |
| Airflow IR CPU Percentage | `generic_data` | `AirflowIntegrationRuntimeCpuPercentage` | Average | % |
| Airflow IR CPU Usage | `generic_data` | `AirflowIntegrationRuntimeCpuUsage` | Average | millicores |
| Airflow IR Dag Bag Size | `generic_data` | `AirflowIntegrationRuntimeDagBagSize` | Total | - |
| Airflow IR Dag Callback Exceptions | `generic_data` | `AirflowIntegrationRuntimeDagCallbackExceptions` | Total | - |
| Airflow IR DAG File Refresh Error | `generic_data` | `AirflowIntegrationRuntimeDAGFileRefreshError` | Total | - |
| Airflow IR DAG Processing Import Errors | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingImportErrors` | Total | - |
| Airflow IR DAG Processing Last Duration | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingLastDuration` | Average | ms |
| Airflow IR DAG Processing Last Run Seconds Ago | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingLastRunSecondsAgo` | Average | s |
| Airflow IR DAG Processing Manager Stalls | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingManagerStalls` | Total | - |
| Airflow IR DAG Processing Processes | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingProcesses` | Total | - |
| Airflow IR DAG Processing Processor Timeouts | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingProcessorTimeouts` | Average | s |
| Airflow IR DAG Processing Total Parse Time | `generic_data` | `AirflowIntegrationRuntimeDAGProcessingTotalParseTime` | Average | s |
| Airflow IR DAG Run Dependency Check | `generic_data` | `AirflowIntegrationRuntimeDAGRunDependencyCheck` | Average | ms |
| Airflow IR DAG Run Duration Failed | `generic_data` | `AirflowIntegrationRuntimeDAGRunDurationFailed` | Average | ms |
| Airflow IR DAG Run Duration Success | `generic_data` | `AirflowIntegrationRuntimeDAGRunDurationSuccess` | Average | ms |
| Airflow IR DAG Run First Task Scheduling Delay | `generic_data` | `AirflowIntegrationRuntimeDAGRunFirstTaskSchedulingDelay` | Average | ms |
| Airflow IR DAG Run Schedule Delay | `generic_data` | `AirflowIntegrationRuntimeDAGRunScheduleDelay` | Average | ms |
| Airflow IR Executor Open Slots | `generic_data` | `AirflowIntegrationRuntimeExecutorOpenSlots` | Total | - |
| Airflow IR Executor Queued Tasks | `generic_data` | `AirflowIntegrationRuntimeExecutorQueuedTasks` | Total | - |
| Airflow IR Executor Running Tasks | `generic_data` | `AirflowIntegrationRuntimeExecutorRunningTasks` | Total | - |
| Airflow IR Job End | `generic_data` | `AirflowIntegrationRuntimeJobEnd` | Total | - |
| Airflow IR Job Heartbeat Failure | `generic_data` | `AirflowIntegrationRuntimeJobHeartbeatFailure` | Total | - |
| Airflow IR Job Start | `generic_data` | `AirflowIntegrationRuntimeJobStart` | Total | - |
| Airflow IR Memory Percentage | `generic_data` | `AirflowIntegrationRuntimeMemoryPercentage` | Average | % |
| Airflow IR Memory Usage | `generic_data` | `AirflowIntegrationRuntimeMemoryUsage` | Average | bytes |
| Airflow IR Node Count | `generic_data` | `AirflowIntegrationRuntimeNodeCount` | Average | - |
| Airflow IR Operator Failures | `generic_data` | `AirflowIntegrationRuntimeOperatorFailures` | Total | - |
| Airflow IR Operator Successes | `generic_data` | `AirflowIntegrationRuntimeOperatorSuccesses` | Total | - |
| Airflow IR Pool Open Slots | `generic_data` | `AirflowIntegrationRuntimePoolOpenSlots` | Total | - |
| Airflow IR Pool Queued Slots | `generic_data` | `AirflowIntegrationRuntimePoolQueuedSlots` | Total | - |
| Airflow IR Pool Running Slots | `generic_data` | `AirflowIntegrationRuntimePoolRunningSlots` | Total | - |
| Airflow IR Pool Starving Tasks | `generic_data` | `AirflowIntegrationRuntimePoolStarvingTasks` | Total | - |
| Airflow IR Scheduler Critical Section Busy | `generic_data` | `AirflowIntegrationRuntimeSchedulerCriticalSectionBusy` | Total | - |
| Airflow IR Scheduler Critical Section Duration | `generic_data` | `AirflowIntegrationRuntimeSchedulerCriticalSectionDuration` | Average | ms |
| Airflow IR Scheduler Failed SLA Email Attempts | `generic_data` | `AirflowIntegrationRuntimeSchedulerFailedSLAEmailAttempts` | Total | - |
| Airflow IR Scheduler Heartbeat | `generic_data` | `AirflowIntegrationRuntimeSchedulerHeartbeat` | Total | - |
| Airflow IR Scheduler Orphaned Tasks Adopted | `generic_data` | `AirflowIntegrationRuntimeSchedulerOrphanedTasksAdopted` | Total | - |
| Airflow IR Scheduler Orphaned Tasks Cleared | `generic_data` | `AirflowIntegrationRuntimeSchedulerOrphanedTasksCleared` | Total | - |
| Airflow IR Scheduler Tasks Executable | `generic_data` | `AirflowIntegrationRuntimeSchedulerTasksExecutable` | Total | - |
| Airflow IR Scheduler Tasks Killed Externally | `generic_data` | `AirflowIntegrationRuntimeSchedulerTasksKilledExternally` | Total | - |
| Airflow IR Scheduler Tasks Running | `generic_data` | `AirflowIntegrationRuntimeSchedulerTasksRunning` | Total | - |
| Airflow IR Scheduler Tasks Starving | `generic_data` | `AirflowIntegrationRuntimeSchedulerTasksStarving` | Total | - |
| Airflow IR Started Task Instances | `generic_data` | `AirflowIntegrationRuntimeStartedTaskInstances` | Total | - |
| Airflow IR Task Instance Created Using Operator | `generic_data` | `AirflowIntegrationRuntimeTaskInstanceCreatedUsingOperator` | Total | - |
| Airflow IR Task Instance Duration | `generic_data` | `AirflowIntegrationRuntimeTaskInstanceDuration` | Average | ms |
| Airflow IR Task Instance Failures | `generic_data` | `AirflowIntegrationRuntimeTaskInstanceFailures` | Total | - |
| Airflow IR Task Instance Finished | `generic_data` | `AirflowIntegrationRuntimeTaskInstanceFinished` | Total | - |
| Airflow IR Task Instance Previously Succeeded | `generic_data` | `AirflowIntegrationRuntimeTaskInstancePreviouslySucceeded` | Total | - |
| Airflow IR Task Instance Successes | `generic_data` | `AirflowIntegrationRuntimeTaskInstanceSuccesses` | Total | - |
| Airflow IR Task Removed From DAG | `generic_data` | `AirflowIntegrationRuntimeTaskRemovedFromDAG` | Total | - |
| Airflow IR Task Restored To DAG | `generic_data` | `AirflowIntegrationRuntimeTaskRestoredToDAG` | Total | - |
| Airflow IR Triggers Blocked Main Thread | `generic_data` | `AirflowIntegrationRuntimeTriggersBlockedMainThread` | Total | - |
| Airflow IR Triggers Failed | `generic_data` | `AirflowIntegrationRuntimeTriggersFailed` | Total | - |
| Airflow IR Triggers Running | `generic_data` | `AirflowIntegrationRuntimeTriggersRunning` | Total | - |
| Airflow IR Triggers Succeeded | `generic_data` | `AirflowIntegrationRuntimeTriggersSucceeded` | Total | - |
| Airflow IR Zombies Killed | `generic_data` | `AirflowIntegrationRuntimeZombiesKilled` | Total | - |

#### Módulos de red virtual administrada

| Módulo | Tipo | Métrica de Azure | Agregación | Unidad |
| --- | --- | --- | --- | --- |
| MVNet IR Copy Available Capacity (%) | `generic_data` | `MVNetIRCopyAvailableCapacityPCT` | Maximum | % |
| MVNet IR Copy Capacity Utilization (%) | `generic_data` | `MVNetIRCopyCapacityUtilization` | Maximum | % |
| MVNet IR Copy Waiting Queue Length | `generic_data` | `MVNetIRCopyWaitingQueueLength` | Average | - |
| MVNet IR External Available Capacity (%) | `generic_data` | `MVNetIRExternalAvailableCapacityPCT` | Maximum | % |
| MVNet IR External Capacity Utilization (%) | `generic_data` | `MVNetIRExternalCapacityUtilization` | Maximum | % |
| MVNet IR External Waiting Queue Length | `generic_data` | `MVNetIRExternalWaitingQueueLength` | Average | - |
| MVNet IR Pipeline Available Capacity (%) | `generic_data` | `MVNetIRPipelineAvailableCapacityPCT` | Maximum | % |
| MVNet IR Pipeline Capacity Utilization (%) | `generic_data` | `MVNetIRPipelineCapacityUtilization` | Maximum | % |
| MVNet IR Pipeline Waiting Queue Length | `generic_data` | `MVNetIRPipelineWaitingQueueLength` | Average | - |

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| Nombre corto de la aplicación | `pandorafms.azure.datafactory` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación Discovery (`.disco`) |
| Sección | Discovery → Cloud |
| Extensión de consola complementaria | `Azure Data Factory Dashboard` (`azure_datafactory_dashboard`) |
