# OpenSearch Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de OpenSearch monitoriza un clúster de OpenSearch a través de su API REST. Lee la salud del clúster, las estadísticas de cada nodo y las estadísticas agregadas de los índices del clúster, y las convierte en agentes y módulos de Pandora FMS.

Una tarea de Discovery genera los agentes según su rol funcional, en lugar de un único agente por clúster:

- **Un agente de clúster** con la salud del clúster: estado, nodos y asignación de shards.
- **Un agente por nodo** con las estadísticas de sistema operativo, proceso, JVM, thread pools, transporte, circuit breakers, cachés y disco de ese nodo.
- **Un agente de métricas primarias** con las estadísticas agregadas de índices (documentos, indexación, búsqueda, merges, segmentos, translog y más) de los shards primarios y de todos los shards.

Cada grupo de agentes es opcional: se elige cuáles de los tres grupos de métricas recoge la tarea y se pueden excluir módulos individuales de cada grupo.

## Preparar

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.opensearch`, versión `1.2` | Objetivo documentado | Versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery al endpoint REST de OpenSearch | `Required` | El addon se conecta a la IP y al puerto configurados en la tarea |
| Acceso a las API Nodes stats, Cluster health e Indices stats | `Required` | El addon llama a estas tres API; cada una solo es necesaria para su grupo de métricas |
| Versiones de OpenSearch | `Not validated` | No se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Not validated` | No se ha registrado una matriz de versiones para este addon |

### Requisitos previos

1. **Conectividad** desde el servidor de Discovery al puerto HTTP(S) de OpenSearch, normalmente `9200`.
2. **Acceso a las API del clúster**. Cuando el clúster exige autenticación, un usuario y una contraseña que puedan leer la salud del clúster, las estadísticas de nodos y las estadísticas de índices. Las credenciales son opcionales: el addon solo se autentica cuando se indican el usuario y la contraseña.
3. **Pandora FMS**: un servidor de Discovery que ejecute la tarea, la consola para definirla y un servidor Tentacle que reciba los datos de los agentes generados.

El addon se distribuye listo para ejecutarse, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.opensearch](https://marketplace.pandorafms.com/entries/pandorafms.opensearch)

Cárguelo en Pandora FMS. Una vez cargado, **OpenSearch** está disponible en la sección de aplicaciones al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones de Discovery y elija **OpenSearch**. La consola presenta los campos en dos pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **OpenSearch Basic** — conexión y transferencia de datos:

    - **OpenSearch IP** y **OpenSearch Port**: dirección y puerto del endpoint REST de OpenSearch. Ambos son obligatorios.
    - **User** y **Password**: credenciales, ambas opcionales.
    - **Verify SSL**: conectar por HTTPS. Consulte [Seguridad de la conexión](#seguridad-de-la-conexion).
    - **Verify Certs**: validar el certificado del servidor.
    - **transfer mode**, **tentacle ip** y **tentacle port**: cómo y dónde se envían los datos de los agentes generados. Rara vez necesitan cambiarse.

    ![Paso OpenSearch Basic del asistente de la tarea](../assets/images/discovery/opensearch/opensearch-task-basic-step.png)

2. **OpenSearch Detailed** — nombres y grupos de métricas:

    - **agent prefix**, **Agent group**, **Custom module prefix** y **Module group**: nombre y agrupación de los agentes y módulos generados.
    - **Primary metrics**, **Nodes Metrics** y **Cluster Metrics**: grupos de métricas a recoger. Activados por defecto.
    - **Exclude primary metrics**, **Exclude nodes metrics** y **Exclude cluster metrics**: módulos que se dejan fuera de cada grupo. Cada uno se muestra solo cuando su grupo de métricas está activado.

    ![Paso OpenSearch Detailed del asistente de la tarea](../assets/images/discovery/opensearch/opensearch-task-detailed-step.png)

El intervalo de ejecución procede del paso genérico de definición de la tarea y se aplica como intervalo de los agentes generados.

### Seguridad de la conexión

- **Verify SSL** controla el protocolo: activado, el addon se conecta por HTTPS; desactivado, por HTTP sin cifrar. Está activado por defecto.
- **Verify Certs** controla el certificado: activado, el addon valida el certificado del servidor; desactivado (por defecto), acepta cualquier certificado. La verificación del nombre de host del certificado está siempre desactivada, incluso con **Verify Certs** activado.
- Con **Verify SSL** activado y **Verify Certs** desactivado el tráfico va cifrado, pero el servidor no se autentica. Use una red de confianza o active **Verify Certs**.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que se completa informa de:

    - **Total Agents**: agentes generados.
    - **Total Modules**: módulos generados entre todos los agentes.

    Los errores al recoger un grupo de métricas se registran en la información de ejecución de la tarea.

    ![Resumen de ejecución de una tarea de Discovery de OpenSearch](../assets/images/discovery/opensearch/opensearch-task-execution-summary.png)

2. **Los agentes.** Un agente de clúster, un agente de métricas primarias y un agente por nodo, según los grupos de métricas activados.
3. **Los módulos.** El agente de clúster tiene, entre otros, `cluster_status`, `number_of_nodes` y `unassigned_shards`; consulte [Módulos por agente](#modulos-por-agente).

## Entender los resultados

### Agentes generados

| Agente | Alias | Se crea cuando | Cardinalidad |
|--------|-------|----------------|--------------|
| Métricas primarias | `<agent prefix>_primary_metrics` | **Primary metrics** activado y las estadísticas se pudieron leer | Uno por tarea |
| Nodo | `<agent prefix>_node_metrics_<nombre del nodo>` | **Nodes Metrics** activado y las estadísticas se pudieron leer | Uno por nodo del clúster |
| Clúster | `<agent prefix>_cluster_metrics` | **Cluster Metrics** activado y las estadísticas se pudieron leer | Uno por tarea |

La identidad del agente se deriva del alias, que incluye el **agent prefix**. Cambiar el prefijo de una tarea crea agentes nuevos en lugar de actualizar los existentes, y el histórico de los agentes anteriores no se traslada. Use un prefijo distinto para cada clúster, de modo que dos tareas nunca escriban en los mismos agentes.

Los agentes se colocan en el **Agent group** cuando se indica, y no tienen dirección, sistema operativo ni agente padre.

### Módulos por agente

El nombre del módulo es el nombre de la métrica, precedido de `<Custom module prefix>_` cuando se indica un prefijo.

| Agente | Módulos |
|--------|---------|
| Clúster | Nombre y estado del clúster (`green`, `yellow` o `red`), número de nodos y de nodos de datos, shards activos, en reubicación, en inicialización, sin asignar y sin asignar con retraso, shards primarios activos, tareas pendientes, fetches sin terminar y porcentaje de shards activos |
| Nodo | CPU, carga media y uso de memoria y swap del sistema operativo; CPU, descriptores de fichero y memoria virtual del proceso; heap, memoria no heap, pools de memoria, hilos y recolección de basura de la JVM; estadísticas de thread pools; conexiones y tráfico de transporte y HTTP; circuit breakers; presión de indexación; caché de peticiones; espacio en disco; y las estadísticas de índices del nodo |
| Métricas primarias | Estadísticas de índices, con prefijo `primaries_` para los shards primarios y `total_` para todos los shards: documentos, tamaño de almacenamiento, indexación, get, búsqueda, merges, refresh, flush, warmer, caché de consultas, fielddata, completion, segmentos, translog, caché de peticiones y recuperación |

La lista completa está en la [Referencia de módulos](#referencia-de-modulos).

## Operar

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El paquete contiene el ejecutable `pandora_opensearch`, que recibe la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_opensearch --conf <PATH_TO_CONFIG>
```

Envía un fichero de datos por agente con el modo de transferencia configurado e imprime un resumen con el total de agentes y módulos creados. Los errores se listan en la misma salida.

Con `--as_server_plugin 1` el addon se ejecuta como plugin de servidor: no imprime resumen e imprime `1` cuando ha creado al menos un agente sin errores y `0` en caso contrario, incluido el caso en que el fichero de configuración no existe.

```bash
./pandora_opensearch --as_server_plugin 1 --conf <PATH_TO_CONFIG>
```

El fichero de configuración contiene la contraseña de OpenSearch en texto plano. Protéjalo con permisos restrictivos.

## Solucionar problemas

El addon no tiene opción de depuración ni modo detallado. Su canal de diagnóstico es la información de ejecución de la tarea o la salida de la ejecución manual.

- **`Error: Could not connect to OpenSearch cluster with <host>:<port>`**: también se informa como `node` o `primary` en lugar de `cluster`, según el grupo de métricas que haya fallado. El endpoint no es alcanzable, el protocolo no coincide (consulte **Verify SSL**) o las credenciales se rechazan. Compruebe la dirección, el puerto y el protocolo desde el servidor de Discovery.
- **`Error: when attempting to obtain cluster statistics`** y **`Error: when attempting to obtain node data`**: la petición llegó al clúster pero falló. El mensaje incluye el error devuelto por OpenSearch, por ejemplo un permiso que falta.
- **`Unable to obtain OpenSearch metrics.`**: ningún grupo de métricas produjo datos. O bien los tres grupos están desactivados o todos fallaron; revise los demás mensajes.
- **`Error create agent <nombre>: <error>`**: no se pudo crear o enviar el agente.
- **Falta un grupo de agentes**: el grupo de métricas está desactivado o su petición falló y la causa está en la información de ejecución. Los demás grupos se generan igualmente.
- **Un agente de nodo falla tras añadir una exclusión**: una exclusión que coincide con el texto `node_name` elimina el nombre del nodo que el addon necesita para crear el agente. Use un texto de exclusión más específico.
- **Han desaparecido más módulos de los esperados**: las exclusiones son expresiones regulares sin distinguir mayúsculas, aplicadas al nombre de la métrica sin el prefijo de módulo, por lo que un texto corto puede coincidir con varios módulos. Consulte [Excluir módulos](#excluir-modulos).
- **Error al leer el fichero de configuración** (`Error file: <ruta> does not exist`, `Error while reading configuration file`): en la ejecución manual, la ruta pasada a `--conf` es incorrecta o el fichero no es legible o no está bien formado.

## Referencia

### Parámetros de la tarea

#### OpenSearch Basic

| Campo | Macro | Tipo | Obligatorio | Por defecto | Descripción |
|-------|-------|------|-------------|-------------|-------------|
| OpenSearch IP | `_opensearchIp_` | cadena | Sí | — | Dirección del endpoint de OpenSearch |
| OpenSearch Port | `_opensearchPort_` | número | Sí | — | Puerto del endpoint, por ejemplo `9200`. Debe ser un número |
| User | `_opensearchUser_` | cadena | No | vacío | La autenticación solo se usa cuando se indican **User** y **Password** |
| Password | `_opensearchPassword_` | contraseña | No | vacío | Contraseña del usuario |
| Verify SSL | `_verifySSL_` | casilla | No | activado | Conecta por HTTPS si está activado y por HTTP sin cifrar si no |
| Verify Certs | `_verifyCerts_` | casilla | No | desactivado | Valida el certificado del servidor. La verificación del nombre de host sigue desactivada |
| transfer mode | `_transferMode_` | cadena | No | `tentacle` | Cómo se entregan los datos de los agentes. El valor por defecto los envía con Tentacle |
| tentacle ip | `_tentacleIp_` | cadena | No | `127.0.0.1` | Servidor Tentacle que recibe los datos de los agentes |
| tentacle port | `_tentaclePort_` | número | No | `41121` | Puerto de Tentacle |

#### OpenSearch Detailed

| Campo | Macro | Tipo | Obligatorio | Por defecto | Descripción |
|-------|-------|------|-------------|-------------|-------------|
| agent prefix | `_prefixAgent_` | cadena | No | vacío | Texto que se antepone al alias de cada agente generado |
| Agent group | `_agentGroup_` | cadena | No | vacío | Grupo de los agentes generados |
| Custom module prefix | `_prefixModuleName_` | cadena | No | vacío | Texto que se antepone al nombre de cada módulo, unido con `_` |
| Module group | `_moduleGroup_` | cadena | No | vacío | Grupo de los módulos generados |
| Primary metrics | `_tokenPrimaryMetrics_` | casilla | No | activado | Recoge las estadísticas agregadas de índices |
| Exclude primary metrics | `_excludePrimaryMetrics_` | área de texto | No | vacío | Módulos a excluir. Se muestra con **Primary metrics** activado |
| Nodes Metrics | `_tokenNodesMetrics_` | casilla | No | activado | Recoge las estadísticas de cada nodo |
| Exclude nodes metrics | `_excludeNodesMetrics_` | área de texto | No | vacío | Módulos a excluir. Se muestra con **Nodes Metrics** activado |
| Cluster Metrics | `_tokenClusterMetrics_` | casilla | No | activado | Recoge la salud del clúster |
| Exclude cluster metrics | `_excludeClusterMetrics_` | área de texto | No | vacío | Módulos a excluir. Se muestra con **Cluster Metrics** activado |

#### Excluir módulos

Cada cuadro de exclusión acepta una lista de entradas separadas por comas. Una entrada elimina todos los módulos de ese grupo cuyo nombre de métrica coincida con ella. La comparación no distingue mayúsculas y encuentra la entrada en cualquier punto del nombre; las entradas se interpretan como expresiones regulares, por lo que una expresión no válida hace fallar el grupo de métricas. Por ejemplo, `unassigned, active` en **Exclude cluster metrics** elimina todos los módulos del clúster cuyo nombre contenga `unassigned` o `active`, incluidos `unassigned_shards`, `active_shards` y `active_primary_shards`.

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Las opciones booleanas aceptan `1`, `true`, `t`, `yes` o `y` para activarse; cualquier otro valor las desactiva.

| Clave | Obligatoria | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| `open_search_ip` | Sí | — | Dirección de OpenSearch |
| `open_search_port` | Sí | — | Puerto de OpenSearch. Debe ser un número |
| `user` | No | vacío | Usuario. La autenticación solo se usa cuando `user` y `password` están ambos indicados |
| `password` | No | vacío | Contraseña |
| `verify_ssl` | No | desactivado | Conectar por HTTPS |
| `verify_certs` | No | desactivado | Validar el certificado del servidor |
| `transfer_mode` | Sí | — | `tentacle` envía los datos con Tentacle |
| `tentacle_ip` | Sí | — | Dirección del servidor Tentacle |
| `tentacle_port` | Sí | — | Puerto del servidor Tentacle |
| `agent_prefix` | No | vacío | Prefijo de los alias de agente |
| `agents_group` | No | vacío | Grupo de los agentes |
| `module_prefix` | No | vacío | Prefijo de los nombres de módulo |
| `module_group` | No | vacío | Grupo de los módulos |
| `token_primary_metrics` | No | desactivado | Recoger el grupo de métricas primarias |
| `exclude_primary_metrics` | No | vacío | Módulos a excluir del grupo de métricas primarias |
| `token_nodes_metrics` | No | desactivado | Recoger el grupo de nodos |
| `exclude_nodes_metrics` | No | vacío | Módulos a excluir del grupo de nodos |
| `token_cluster_metrics` | No | desactivado | Recoger el grupo de clúster |
| `exclude_cluster_metrics` | No | vacío | Módulos a excluir del grupo de clúster |
| `interval` | No | `0` | Intervalo de los agentes, en segundos. Indíquelo explícitamente: un valor ausente se lee como `0` |

A diferencia de la tarea de Discovery, los grupos de métricas están desactivados cuando falta su clave.

Ejemplo:

```ini
open_search_ip          = <OPENSEARCH_HOST>
open_search_port        = 9200
user                    = <USERNAME>
password                = <PASSWORD>
verify_ssl              = true
verify_certs            = false
transfer_mode           = tentacle
tentacle_ip             = <TENTACLE_SERVER_IP>
tentacle_port           = 41121
agent_prefix            = <AGENT_PREFIX>
module_prefix           = opensearch
module_group            = <MODULE_GROUP>
token_primary_metrics   = 0
token_nodes_metrics     = 0
token_cluster_metrics   = 1
exclude_cluster_metrics = unassigned, active
interval                = 300
```

### Referencia de módulos

Los nombres se muestran sin el **Custom module prefix**. Un módulo se crea solo si no está excluido.

**Agente de clúster**

`cluster_name`, `cluster_status`, `number_of_nodes`, `number_of_data_nodes`, `active_primary_shards`, `active_shards`, `relocating_shards`, `initializing_shards`, `unassigned_shards`, `delayed_unassigned_shards`, `number_of_pending_tasks`, `number_of_in_flight_fetch`, `active_shards_percent_as_number`.

**Agente de nodo**

| Grupo | Nombres de módulo |
|-------|-------------------|
| Sistema operativo | `os_timestamp`, `os_cpu_percent`, `os_cpu_load_average_1m`, `os_cpu_load_average_5m`, `os_cpu_load_average_15m`, `os_mem_total_in_bytes`, `os_mem_free_in_bytes`, `os_mem_used_in_bytes`, `os_mem_free_percent`, `os_mem_used_percent`, `os_swap_total_in_bytes`, `os_swap_free_in_bytes`, `os_swap_used_in_bytes` |
| Proceso | `process_timestamp`, `process_open_file_descriptors`, `process_max_file_descriptors`, `process_cpu_percent`, `process_cpu_total_time`, `process_mem_total_virtual_in_bytes` |
| JVM | `jvm_timestamp`, `jvm_uptime_time`, `jvm_mem_heap_*` (usado, porcentaje usado, comprometido, máximo), `jvm_mem_non_heap_*` (usado, comprometido), `jvm_mem_pools_<young\|old\|survivor>_*` (usado, máximo, pico usado, pico máximo), `jvm_threads_count`, `jvm_threads_peak_count`, `jvm_gc_collectors_<young\|old\|G1_Concurrent_GC>_collection_count` y `_collection_time` |
| Thread pools | `thread_pool_<pool>_threads`, `_queue`, `_active`, `_rejected`, `_largest` y `_completed` para los pools `fetch_shard_started`, `fetch_shard_store`, `flush`, `force_merge`, `generic`, `get`, `index_searcher`, `listener`, `management`, `refresh`, `search`, `snapshot`, `warmer` y `write`; además de `thread_pool_index_searcher_total_wait_time_in_nanos` y `thread_pool_search_total_wait_time_in_nanos` |
| Transporte y HTTP | `transport_server_open`, `transport_total_outbound_connections`, `transport_rx_count`, `transport_rx_size_in_bytes`, `transport_tx_count`, `transport_tx_size_in_bytes`, `http_current_open`, `http_total_opened` |
| Circuit breakers | `breakers_<fielddata\|request\|in_flight_requests\|parent>_` seguido de `limit_size`, `limit_size_in_bytes`, `estimated_size`, `estimated_size_in_bytes`, `overhead` y `tripped` |
| Presión de indexación | `indexing_pressure_memory_current_*`, `indexing_pressure_memory_total_*` e `indexing_pressure_memory_limit_in_bytes` |
| Caché de peticiones | `caches_request_cache_size_in_bytes`, `_evictions`, `_hit_count`, `_miss_count`, `_item_count` y `_store_name` |
| Disco | `fs_disk_avail`, `fs_disk_used`, `fs_disk_percent` |
| Estadísticas de índices | Los nombres listados para el agente de métricas primarias, con un `_` inicial en lugar del prefijo `primaries_` o `total_` |

**Agente de métricas primarias**

Cada nombre siguiente aparece dos veces, una con el prefijo `primaries_` y otra con `total_`.

| Grupo | Nombres de módulo (tras el prefijo) |
|-------|-------------------------------------|
| Documentos y almacenamiento | `docs_count`, `docs_deleted`, `store_size_in_bytes`, `store_reserved_in_bytes` |
| Indexación | `indexing_index_total`, `indexing_time`, `indexing_current`, `indexing_failed`, `indexing_delete_total`, `indexing_delete_time`, `indexing_delete_current`, `indexing_noop_update_total`, `indexing_throttle_time` |
| Get | `get_total`, `get_time`, `get_exists_total`, `get_exists_time`, `get_missing_total`, `get_missing_time`, `get_current` |
| Búsqueda | `search_open_contexts`, `search_query_*`, `search_concurrent_query_*`, `search_concurrent_avg_slice_count`, `search_fetch_*`, `search_scroll_*`, `search_point_time_*`, `search_suggest_*`, `search_search_idle_reactivate_count_total` |
| Merges | `merges_current`, `merges_current_docs`, `merges_current_size_in_bytes`, `merges_total`, `merges_total_time`, `merges_total_docs`, `merges_total_size_in_bytes`, `merges_total_stopped_time`, `merges_total_throttled_time`, `merges_total_auto_throttle_in_bytes` |
| Refresh, flush y warmer | `refresh_total`, `refresh_total_time`, `refresh_external_total`, `refresh_external_total_time`, `refresh_listeners`, `flush_total`, `flush_periodic`, `flush_total_time`, `warmer_current`, `warmer_total`, `warmer_total_time` |
| Cachés | `query_cache_*` (tamaño de memoria, total, aciertos, fallos, tamaño de caché, número de cachés, evicciones), `fielddata_memory_size_in_bytes`, `fielddata_evictions`, `completion_size_in_bytes`, `request_cache_*` (tamaño de memoria, evicciones, aciertos, fallos) |
| Segmentos | `segments_count`, `segments_memory_in_bytes` y los módulos de memoria por estructura (`segments_terms_memory_in_bytes`, `segments_stored_fields_memory_in_bytes`, `segments_term_vectors_memory_in_bytes`, `segments_norms_memory_in_bytes`, `segments_points_memory_in_bytes`, `segments_doc_values_memory_in_bytes`, `segments_index_writer_memory_in_bytes`, `segments_version_map_memory_in_bytes`, `segments_fixed_bit_set_memory_in_bytes`), `segments_max_unsafe_auto_id_timestamp` |
| Translog y recuperación | `translog_operations`, `translog_size_in_bytes`, `translog_uncommitted_operations`, `translog_uncommitted_size_in_bytes`, `translog_earliest_last_modified_age`, `recovery_current_as_source`, `recovery_current_as_target`, `recovery_throttle_time` |

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | OpenSearch |
| Identificador | `pandorafms.opensearch` |
| Versión | `1.2` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.opensearch](https://marketplace.pandorafms.com/entries/pandorafms.opensearch), actualizada el 2026-02-26 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
