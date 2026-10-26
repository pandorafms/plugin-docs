# Elasticsearch Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Elasticsearch monitoriza un clúster de Elasticsearch a través de su API REST. En lugar de crear un único agente, divide la monitorización por rol funcional y crea un agente por rol:

- **Un agente de métricas primarias** con las estadísticas de indexación, búsqueda, fusiones, cachés, segmentos y translog de todos los índices, una vez para los shards primarios y otra para el total de shards (primarios y réplicas).
- **Un agente de clúster** con la salud del clúster: estado, número de nodos y asignación de shards.
- **Un agente por nodo** con métricas de sistema operativo, proceso, JVM, thread pools, transporte, HTTP, circuit breakers, cachés y disco, además de las estadísticas de índices que ve ese nodo.

Cada rol es opcional y se activa o desactiva en la tarea de Discovery. Se pueden excluir métricas concretas por nombre.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.elastic`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery al puerto HTTP(S) de Elasticsearch | `Requerido` | El addon consulta las API de salud del clúster, estadísticas de nodos y estadísticas de índices |
| Acceso al clúster de Elasticsearch con permiso de lectura sobre esas API | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Versiones del servidor Elasticsearch | `Sin validar` | No se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery al nodo de Elasticsearch al que apunta la tarea (dirección IP y puerto, normalmente `9200`).
2. **Credenciales** cuando el clúster exige autenticación. El usuario y la contraseña son opcionales en la tarea; el addon solo usa autenticación básica cuando se indican ambos. La cuenta debe poder llamar a las API de salud del clúster, estadísticas de nodos y estadísticas de índices. Esta página no prescribe un rol más restringido, porque no se ha registrado una declaración oficial de los privilegios mínimos.
3. **Pandora FMS**: un servidor de Discovery que ejecute la tarea y la consola para definirla. Por defecto el addon envía los datos de los agentes con Tentacle, por lo que la dirección del servidor Tentacle debe ser alcanzable desde el servidor de Discovery.

El paquete del addon incluye todo lo necesario para ejecutarse, así que no hay que instalar nada más en el servidor de Discovery.

### Instalar el addon

Descargue el paquete `.disco` de la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.elastic](https://marketplace.pandorafms.com/entries/pandorafms.elastic)

Cárguelo en **Management > Discovery > Manage disco packages**.

![Manage disco packages con el paquete Elasticsearch cargado](../assets/images/discovery/elasticsearch/manage-disco-packages.png)

Una vez cargado, **Elasticsearch** está disponible en **Management > Discovery > Applications** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management > Discovery > Applications > Elasticsearch**. Tras la definición genérica de la tarea (nombre, servidor de Discovery, grupo, intervalo), la consola presenta dos pasos. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

![Definición de la tarea de Elasticsearch, con Elasticsearch en Applications](../assets/images/discovery/elasticsearch/task-definition-and-menu.png)

1. **ElasticSearch Basic** — conexión y transferencia:

    - **ElasticSearch IP** y **ElasticSearch Port**: dirección del nodo de Elasticsearch. Ambos son obligatorios.
    - **User** y **Password**: credenciales opcionales.
    - **Verify SSL**: conecta por HTTPS si está activado y por HTTP si no. Activado por defecto.
    - **Verify Certs**: valida el certificado TLS del servidor. Desactivado por defecto.
    - **transfer mode**, **tentacle ip** y **tentacle port**: cómo llegan los datos de los agentes a Pandora FMS. Rara vez hay que cambiarlos.

    ![Paso ElasticSearch Basic del asistente de la tarea](../assets/images/discovery/elasticsearch/task-step-basic.png)

2. **ElasticSearch Detailed** — nombres y selección de métricas:

    - **agent prefix**, **Agent group**, **Custom module prefix** y **Module group**: nombres aplicados a los agentes y módulos generados.
    - **Primary metrics**, **Nodes Metrics** y **Cluster Metrics**: eligen qué agentes se crean. Las tres están activadas por defecto.
    - **Exclude primary metrics**, **Exclude nodes metrics** y **Exclude cluster metrics**: se muestran cuando está activada la opción de métricas correspondiente. Nombres de los módulos que no se deben crear, consulte [Excluir métricas](#excluir-metricas).

    ![Paso ElasticSearch Detailed del asistente de la tarea](../assets/images/discovery/elasticsearch/task-step-detailed.png)

El intervalo de la tarea definido en el paso genérico pasa a ser el intervalo de los agentes generados.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que termina informa de **Total Agents** y **Total Modules**. Los errores encontrados al consultar el clúster se registran en la información de ejecución de la tarea.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea de Discovery de Elasticsearch con Total Agents y Total Modules, capturado con la versión actual del addon. -->

2. **Los agentes.** Un agente de métricas primarias, un agente de clúster y un agente por nodo, según las opciones de métricas activadas. Con las tres opciones activadas y un clúster de un solo nodo la tarea crea tres agentes.
3. **Los módulos.** Abra el agente de clúster: tiene 13 módulos, como `cluster_status` y `number_of_nodes`.

    ![Módulos del agente de clúster](../assets/images/discovery/elasticsearch/cluster-agent-modules.png)

## Entender los resultados

### Agentes generados

| Agente | Alias | Se crea cuando | Módulos |
|--------|-------|----------------|---------|
| Métricas primarias | `<agent prefix>_primary_metrics` | **Primary metrics** está activado | 192 |
| Clúster | `<agent prefix>_cluster_metrics` | **Cluster Metrics** está activado | 13 |
| Nodo | `<agent prefix>_node_metrics_<nombre del nodo>` | **Nodes Metrics** está activado; uno por nodo que informa el clúster | 285 |

El nombre del agente se deriva del alias, por lo que la identidad del agente depende solo del **agent prefix**, del rol (y del nombre del nodo), no de la tarea ni de la dirección del clúster. Use un **agent prefix** distinto para cada clúster; dos tareas con el mismo prefijo escriben en los mismos agentes. Cuando **agent prefix** está vacío, el alias empieza por un guion bajo, por ejemplo `_cluster_metrics`.

Todos los agentes se crean en el **Agent group** si se indica, tienen la descripción `Created by elasticsearch plugin` y no tienen padre, sistema operativo ni dirección. Los recuentos de módulos anteriores son los previos a aplicar exclusiones y **Custom module prefix**.

![Módulos del agente de métricas primarias](../assets/images/discovery/elasticsearch/primary-agent-modules.png)

![Módulos de un agente de nodo](../assets/images/discovery/elasticsearch/node-agent-modules.png)

### Grupos de módulos

- **Agente de métricas primarias**: las estadísticas de todos los índices (`_all`) de los shards primarios, con nombre `primaries_<métrica>`, y de todos los shards, con nombre `total_<métrica>`. Ambos conjuntos contienen las mismas 96 métricas.
- **Agente de clúster**: nombre y estado de salud del clúster, nodos, asignación de shards y tareas pendientes.
- **Agente de nodo**: sistema operativo, proceso, JVM, thread pools, transporte, HTTP, circuit breakers, indexing pressure y cachés del nodo, el espacio en disco de sus rutas de datos y las estadísticas de índices del nodo (las mismas 96 métricas, con nombre `_<métrica>`).

Cuando se indica **Custom module prefix**, cada nombre de módulo pasa a ser `<prefijo>_<nombre>`. **Module group** se aplica a todos los módulos.

## Operación

### Excluir métricas

Cada campo de exclusión acepta una lista **separada por comas**. Cada entrada se compara, sin distinguir mayúsculas, como expresión regular contra el nombre del módulo; un módulo cuyo nombre coincide con cualquier entrada no se crea. Como la comparación es una búsqueda y no una igualdad exacta, `cache` elimina todos los módulos que contengan `cache` en el nombre, y `^total_` elimina solo los módulos que empiezan por `total_`.

- Separe las entradas con comas. Una lista escrita con una entrada por línea no se divide en varias entradas.
- Las exclusiones se evalúan sobre el nombre del módulo **antes** de añadir el **Custom module prefix**.
- Una expresión regular no válida hace fallar la consulta de ese rol; el error se registra en la información de ejecución y no se crea ningún agente de ese rol.
- En el rol de nodos, no use un patrón que coincida con el texto `node_name`. El nombre del nodo viaja en una entrada interna del mismo conjunto; si se excluye, la creación de agentes se detiene con `Error create agent <prefijo>: 'node_name'`: no se crea ningún agente de nodo y tampoco los agentes de los roles siguientes (el agente de clúster).

### Ejecución manual

El paquete incluye el ejecutable `bin/pandora_elasticsearch`, que puede ejecutarse fuera de una tarea de Discovery con un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_elasticsearch --conf <PATH_TO_CONFIG>
```

Envía un fichero de datos por agente e imprime un resumen JSON:

```json
{"summary": {"Total Agents": 1, "Total Modules": 13}}
```

![Ejecución manual que imprime el resumen JSON](../assets/images/discovery/elasticsearch/manual-run-json-summary.png)

Con `--as_server_plugin 1` el ejecutable imprime solo `1` cuando se creó al menos un agente y no se registró ningún error, y `0` en caso contrario. Use esta forma al ejecutarlo como plugin de servidor:

```bash
./pandora_elasticsearch --as_server_plugin 1 --conf <PATH_TO_CONFIG>
```

![Ejecución manual con --as_server_plugin que imprime 1](../assets/images/discovery/elasticsearch/manual-run-server-plugin-output.png)

El fichero de configuración contiene la contraseña en texto claro. Protéjalo con permisos restrictivos.

## Resolución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es la información de la ejecución de la tarea (o la salida JSON de una ejecución manual).

- **`Error file: <ruta> does not exist`**: ejecución manual con una ruta `--conf` inexistente o vacía.
- **`Error while reading configuration file: ...`**: el fichero de configuración no se puede interpretar.
- **`Error: Could not connect to OpenSearch primary|node|cluster with <host>:<puerto>`**: no se pudo alcanzar el clúster para ese rol. El texto menciona OpenSearch aunque el destino sea Elasticsearch. Compruebe la IP, el puerto, el cortafuegos y el valor de **Verify SSL**: un clúster que sirve HTTPS necesita tenerlo activado, uno que sirve HTTP plano necesita desactivarlo.
- **`Error: The index does not exist in the cluster.`**: la consulta de métricas primarias no encontró las estadísticas solicitadas.
- **`Error: when attempting to obtain node data ...` o `... cluster statistics ...`**: el clúster respondió con un error, por ejemplo porque la cuenta no tiene permiso. El mensaje incluye el error devuelto por el clúster.
- **`Unable to obtain OpenSearch metrics.`**: ningún rol produjo datos. O bien las tres opciones de métricas están desactivadas, o todas las consultas fallaron.
- **Menos agentes de los esperados**: un rol cuya consulta falla se omite sin detener los demás, por lo que la tarea puede terminar con solo algunos agentes. Lea la información de ejecución para ver qué rol falla.
- **La autenticación falla aunque se indicaron credenciales**: una contraseña que contiene el carácter `%` no se lee correctamente del fichero de configuración que genera la tarea, y el addon conecta entonces sin credenciales. Evite `%` en la contraseña de la cuenta usada por la tarea.
- **`Error create agent <prefijo>: ...`**: falló la construcción del agente de un rol después de leer los datos. En el rol de nodos suele seguir a un patrón de exclusión, consulte [Excluir métricas](#excluir-metricas).

## Referencia

### Parámetros de la tarea

#### ElasticSearch Basic

| Campo | Macro | Tipo | Obligatorio | Por defecto | Notas |
|-------|-------|------|-------------|-------------|-------|
| ElasticSearch IP | `_elasticsearchIp_` | cadena | Sí | — | Dirección del nodo de Elasticsearch |
| ElasticSearch Port | `_elasticsearchPort_` | número | Sí | — | Puerto HTTP(S), normalmente `9200` |
| User | `_elasticsearchUser_` | cadena | No | vacío | Se usa solo junto con **Password** |
| Password | `_elasticsearchPassword_` | contraseña | No | vacío | Se usa solo junto con **User** |
| Verify SSL | `_verifySSL_` | casilla | No | activado | Activado conecta por HTTPS, desactivado por HTTP |
| Verify Certs | `_verifyCerts_` | casilla | No | desactivado | Valida el certificado TLS del servidor |
| transfer mode | `_transferMode_` | cadena | No | `tentacle` | Cómo se envían los datos de los agentes. `tentacle` los envía con el cliente Tentacle; otros valores se pasan a las herramientas de transferencia del paquete y no se han validado para esta página |
| tentacle ip | `_tentacleIp_` | cadena | No | `127.0.0.1` | Dirección del servidor Tentacle |
| tentacle port | `_tentaclePort_` | número | No | `41121` | Puerto del servidor Tentacle |

#### ElasticSearch Detailed

| Campo | Macro | Tipo | Obligatorio | Por defecto | Notas |
|-------|-------|------|-------------|-------------|-------|
| agent prefix | `_prefixAgent_` | cadena | No | vacío | Prefijo de los alias de los agentes |
| Agent group | `_agentGroup_` | cadena | No | vacío | Grupo asignado a los agentes |
| Custom module prefix | `_prefixModuleName_` | cadena | No | vacío | Prefijo de cada nombre de módulo |
| Module group | `_moduleGroup_` | cadena | No | vacío | Grupo asignado a los módulos |
| Primary metrics | `_tokenPrimaryMetrics_` | casilla | No | activado | Crea el agente de métricas primarias |
| Exclude primary metrics | `_excludePrimaryMetrics_` | área de texto | No | vacío | Se muestra con **Primary metrics** activado |
| Nodes Metrics | `_tokenNodesMetrics_` | casilla | No | activado | Crea un agente por nodo |
| Exclude nodes metrics | `_excludeNodesMetrics_` | área de texto | No | vacío | Se muestra con **Nodes Metrics** activado |
| Cluster Metrics | `_tokenClusterMetrics_` | casilla | No | activado | Crea el agente de clúster |
| Exclude cluster metrics | `_excludeClusterMetrics_` | área de texto | No | vacío | Se muestra con **Cluster Metrics** activado |

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea, sin cabecera de sección. Una clave ausente se lee como vacía (`0` en números, desactivada en booleanos). Los valores booleanos aceptan `yes`, `true`, `t`, `y` y `1`; cualquier otro valor es desactivado.

| Clave | Obligatoria | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| `elastic_search_ip` | Sí | ninguno | Dirección del nodo de Elasticsearch |
| `elastic_search_port` | Sí | ninguno | Puerto HTTP(S) |
| `user` | No | ninguno | Usuario de autenticación básica; se usa solo junto con `password` |
| `password` | No | ninguno | Contraseña de autenticación básica. No use `%` |
| `verify_ssl` | No | desactivado | Activado conecta por HTTPS, desactivado por HTTP. Indíquelo siempre: una clave ausente significa HTTP |
| `verify_certs` | No | desactivado | Valida el certificado TLS del servidor |
| `transfer_mode` | Sí | ninguno | Modo de transferencia, por ejemplo `tentacle` |
| `tentacle_ip` | Con Tentacle | ninguno | Dirección del servidor Tentacle |
| `tentacle_port` | Con Tentacle | ninguno | Puerto del servidor Tentacle |
| `agent_prefix` | No | vacío | Prefijo de los alias de los agentes |
| `agents_group` | No | vacío | Grupo de los agentes |
| `module_prefix` | No | vacío | Prefijo de los nombres de módulo |
| `module_group` | No | vacío | Grupo de los módulos |
| `token_primary_metrics` | No | desactivado | Crea el agente de métricas primarias |
| `exclude_primary_metrics` | No | vacío | Patrones de exclusión separados por comas |
| `token_nodes_metrics` | No | desactivado | Crea los agentes de nodo |
| `exclude_nodes_metrics` | No | vacío | Patrones de exclusión separados por comas |
| `token_cluster_metrics` | No | desactivado | Crea el agente de clúster |
| `exclude_cluster_metrics` | No | vacío | Patrones de exclusión separados por comas |
| `interval` | No | `0` | Intervalo de los agentes, en segundos. Indíquelo siempre, por ejemplo `300` |

Ejemplo:

```ini
elastic_search_ip = <ELASTICSEARCH_HOST>
elastic_search_port = 9200
user = <USERNAME>
password = <PASSWORD>
verify_ssl = true
verify_certs = false
transfer_mode = tentacle
tentacle_ip = <TENTACLE_SERVER_IP>
tentacle_port = 41121
agent_prefix = prod
module_prefix =
token_primary_metrics = 1
token_nodes_metrics = 1
exclude_nodes_metrics = thread_pool, breakers
token_cluster_metrics = 1
exclude_cluster_metrics = delayed
interval = 300
```

### Módulos del agente de clúster

| Módulo | Descripción |
|--------|-------------|
| `cluster_name` | Nombre del clúster |
| `cluster_status` | Salud del clúster: `green`, `yellow` o `red` |
| `number_of_nodes` | Nodos del clúster |
| `number_of_data_nodes` | Nodos de datos del clúster |
| `active_primary_shards` | Shards primarios activos |
| `active_shards` | Shards activos, primarios y réplicas |
| `relocating_shards` | Shards en reubicación |
| `initializing_shards` | Shards en inicialización |
| `unassigned_shards` | Shards sin asignar |
| `delayed_unassigned_shards` | Shards sin asignar retrasados |
| `number_of_pending_tasks` | Tareas pendientes del clúster |
| `number_of_in_flight_fetch` | Fetch sin terminar |
| `active_shards_percent_as_number` | Porcentaje de shards activos, en `%` |

### Módulos de estadísticas de índices

El agente de métricas primarias crea estas 96 métricas dos veces, con nombre `primaries_<métrica>` y `total_<métrica>`. El agente de nodo las crea una vez, con nombre `_<métrica>`. Las métricas de tiempo están en milisegundos y las de tamaño en bytes, como indica el nombre de la métrica.

| Grupo | Métricas |
|-------|----------|
| Documentos | `docs_count`, `docs_deleted` |
| Almacén | `store_size_in_bytes`, `store_reserved_in_bytes` |
| Indexación | `indexing_index_total`, `indexing_time`, `indexing_current`, `indexing_failed`, `indexing_delete_total`, `indexing_delete_time`, `indexing_delete_current`, `indexing_noop_update_total`, `indexing_throttle_time` |
| Get | `get_total`, `get_time`, `get_exists_total`, `get_exists_time`, `get_missing_total`, `get_missing_time`, `get_current` |
| Búsqueda | `search_open_contexts`, `search_query_total`, `search_query_time`, `search_query_current`, `search_concurrent_query_total`, `search_concurrent_query_time`, `search_concurrent_query_current`, `search_concurrent_avg_slice_count`, `search_fetch_total`, `search_fetch_time`, `search_fetch_current`, `search_scroll_total`, `search_scroll.time`, `search_scroll_current`, `search_point_time_total`, `search_point_time_time`, `search_point_time_current`, `search_suggest_total`, `search_suggest_time`, `search_suggest_current`, `search_search_idle_reactivate_count_total` |
| Fusiones | `merges_current`, `merges_current_docs`, `merges_current_size_in_bytes`, `merges_total`, `merges_total_time`, `merges_total_docs`, `merges_total_size_in_bytes`, `merges_total_stopped_time`, `merges_total_throttled_time`, `merges_total_auto_throttle_in_bytes` |
| Refresh | `refresh_total`, `refresh_total_time`, `refresh_external_total`, `refresh_external_total_time`, `refresh_listeners` |
| Flush | `flush_total`, `flush_periodic`, `flush_total_time` |
| Warmer | `warmer_current`, `warmer_total`, `warmer_total_time` |
| Caché de consultas | `query_cache_memory_size_in_bytes`, `query_cache_total_count`, `query_cache_hit_count`, `query_cache_miss_count`, `query_cache_cache_size`, `query_cache_cache_count`, `query_cache_evictions` |
| Field data y completion | `fielddata_memory_size_in_bytes`, `fielddata_evictions`, `completion_size_in_bytes` |
| Segmentos | `segments_count`, `segments_memory_in_bytes`, `segments_terms_memory_in_bytes`, `segments_stored_fields_memory_in_bytes`, `segments_term_vectors_memory_in_bytes`, `segments_norms_memory_in_bytes`, `segments_points_memory_in_bytes`, `segments_doc_values_memory_in_bytes`, `segments_index_writer_memory_in_bytes`, `segments_version_map_memory_in_bytes`, `segments_fixed_bit_set_memory_in_bytes`, `segments_max_unsafe_auto_id_timestamp` |
| Translog | `translog_operations`, `translog_size_in_bytes`, `translog_uncommitted_operations`, `translog_uncommitted_size_in_bytes`, `translog_earliest_last_modified_age` |
| Caché de peticiones | `request_cache_memory_size_in_bytes`, `request_cache_evictions`, `request_cache_hit_count`, `request_cache_miss_count` |
| Recuperación | `recovery_current_as_source`, `recovery_current_as_target`, `recovery_throttle_time` |

### Módulos del agente de nodo

Además de los 96 módulos de estadísticas de índices (`_<métrica>`), cada agente de nodo tiene estos 189 módulos.

| Grupo | Módulos |
|-------|---------|
| Sistema operativo (13) | `os_timestamp`, `os_cpu_percent`, `os_cpu_load_average_1m`, `os_cpu_load_average_5m`, `os_cpu_load_average_15m`, `os_mem_total_in_bytes`, `os_mem_free_in_bytes`, `os_mem_used_in_bytes`, `os_mem_free_percent`, `os_mem_used_percent`, `os_swap_total_in_bytes`, `os_swap_free_in_bytes`, `os_swap_used_in_bytes` |
| Proceso (6) | `process_timestamp`, `process_open_file_descriptors`, `process_max_file_descriptors`, `process_cpu_percent`, `process_cpu_total_time`, `process_mem_total_virtual_in_bytes` |
| JVM (28) | `jvm_timestamp`, `jvm_uptime_time`, `jvm_mem_heap_used_in_bytes`, `jvm_mem_heap_used_percent`, `jvm_mem_heap_committed_in_bytes`, `jvm_mem_heap_max_in_bytes`, `jvm_mem_non_heap_used_in_bytes`, `jvm_mem_non_heap_committed_in_bytes`, `jvm_mem_pools_<pool>_<valor>` para los pools `young`, `old` y `survivor` y los valores `used_in_bytes`, `max_in_bytes`, `peak_used_in_bytes`, `peak_max_in_bytes` (12), `jvm_threads_count`, `jvm_threads_peak_count`, `jvm_gc_collectors_<collector>_collection_count` y `jvm_gc_collectors_<collector>_collection_time` para los collectors `young`, `G1_Concurrent_GC` y `old` (6) |
| Thread pools (86) | `thread_pool_<pool>_<valor>` para los pools `fetch_shard_started`, `fetch_shard_store`, `flush`, `force_merge`, `generic`, `get`, `index_searcher`, `listener`, `management`, `refresh`, `search`, `snapshot`, `warmer` y `write`, y los valores `threads`, `queue`, `active`, `rejected`, `largest` y `completed` (84); más `thread_pool_index_searcher_total_wait_time_in_nanos` y `thread_pool_search_total_wait_time_in_nanos` |
| Transporte (6) | `transport_server_open`, `transport_total_outbound_connections`, `transport_rx_count`, `transport_rx_size_in_bytes`, `transport_tx_count`, `transport_tx_size_in_bytes` |
| HTTP (2) | `http_current_open`, `http_total_opened` |
| Circuit breakers (24) | `breakers_<breaker>_<valor>` para los breakers `request`, `fielddata`, `in_flight_requests` y `parent` y los valores `limit_size_in_bytes`, `limit_size`, `estimated_size_in_bytes`, `estimated_size`, `overhead` y `tripped` |
| Indexing pressure (14) | `indexing_pressure_memory_current_combined_coordinating_and_primary_in_bytes`, `indexing_pressure_memory_current_coordinating_in_bytes`, `indexing_pressure_memory_current_primary_in_bytes`, `indexing_pressure_memory_current_replica_in_bytes`, `indexing_pressure_memory_current_all_in_bytes`, `indexing_pressure_memory_total_combined_coordinating_and_primary_in_bytes`, `indexing_pressure_memory_total_coordinating_in_bytes`, `indexing_pressure_memory_total_primary_in_bytes`, `indexing_pressure_memory_total_replica_in_bytes`, `indexing_pressure_memory_total_all_in_bytes`, `indexing_pressure_memory_total_coordinating_rejections`, `indexing_pressure_memory_total_primary_rejections`, `indexing_pressure_memory_total_replica_rejections`, `indexing_pressure_memory_limit_in_bytes` |
| Cachés (6) | `caches_request_cache_size_in_bytes`, `caches_request_cache_evictions`, `caches_request_cache_hit_count`, `caches_request_cache_miss_count`, `caches_request_cache_item_count`, `caches_request_cache_store_name` |
| Disco (4) | `fs_disk_total`, `fs_disk_avail`, `fs_disk_used` (bytes) y `fs_disk_percent` (`%`), agregados sobre las rutas de datos del nodo |

Los valores que el clúster no informa para un nodo se crean con el valor `0`.

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Elasticsearch |
| Identificador en el Marketplace | `pandorafms.elastic` |
| Nombre corto del paquete | `pandorafms.elasticsearch` |
| Versión | `1.0` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.elastic](https://marketplace.pandorafms.com/entries/pandorafms.elastic), actualizada el 2026-02-05 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
