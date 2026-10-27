# Redis Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Redis monitoriza instancias de Redis. Se conecta a cada instancia que declares, lee sus estadísticas y las convierte en módulos de Pandora FMS: uso de memoria, clientes conectados, comandos ejecutados, persistencia, replicación, CPU, latencia, keyspace y más. También puede ejecutar tus propias consultas de búsqueda sobre un índice de búsqueda de Redis y publicar cada resultado como un módulo.

El addon crea **un agente por instancia de Redis**, de modo que una única tarea de Discovery puede cubrir tantas instancias como cadenas de conexión indiques.

## Preparar

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Versión `1.0` del addon (`pandorafms.redis`) | Objetivo documentado | La versión que describe esta página. Consulta [Identidad del addon](#identidad-del-addon) |
| Versiones de Pandora FMS | `Sin validar` | El Marketplace muestra un aviso general para todas sus integraciones, no una declaración específica de este addon |
| Conectividad de red desde el servidor de Discovery a cada instancia de Redis | `Requerido` | El addon abre una conexión por instancia |
| Capacidad de búsqueda de Redis (`FT.SEARCH`) en la instancia | `Requerido` solo para consultas personalizadas | Prerrequisito de la función **Custom queries**, no una declaración de compatibilidad |
| Cualquier versión, edición o modo de despliegue concreto de Redis | `Sin validar` | No hay registro de pruebas para una matriz de versiones |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo |

### Prerrequisitos

1. **Acceso de red** desde el servidor de Discovery a cada host y puerto de Redis.
2. **Una cuenta de Redis que pueda conectarse y leer la información del servidor.** Si la instancia usa ACL, el usuario debe poder ejecutar al menos `PING` e `INFO`. Las consultas personalizadas necesitan además permiso para el comando de búsqueda que usan (`FT.SEARCH`).
3. **Un índice de búsqueda de Redis**, solo si defines consultas personalizadas. El índice debe existir ya en la instancia.
4. **Pandora FMS**: un servidor de Discovery que ejecute la tarea y la consola para definirla.

Ejemplo de usuario ACL que puede ejecutar la recogida base:

```
ACL SETUSER <USERNAME> on ><PASSWORD> ~* +info +ping
```

Escribir una contraseña en un comando la expone en el historial de la shell. Es preferible definirla desde un archivo de configuración protegido o una sesión interactiva del cliente.

### Disponibilidad y licencia

La entrada del Marketplace indica que la descarga de este addon está limitada a usuarios con licencia. El Marketplace muestra la versión `1.0`, actualizada por última vez el 2026-01-12.

### Instalar el addon

Carga el paquete `.disco` desde el Marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/](https://marketplace.pandorafms.com/)

Una vez cargado, la aplicación **Redis** está disponible al crear tareas de Discovery.

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Applications → Redis**. La consola presenta los campos en tres pasos. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Redis base**: qué instancias leer y adónde enviar los datos:

    - **Connection strings**: una conexión de Redis por línea. Consulta [Cadenas de conexión](#cadenas-de-conexion).
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: adónde se envían los datos de los agentes generados. Normalmente conservan sus valores por defecto.

    ![Paso Redis base del asistente con las cadenas de conexión y los campos de Tentacle](../assets/images/discovery/redis/redis-task-connections-tentacle.png)

2. **redis detailed**: da forma al resultado:

    - **Max threads**, prefijos de módulos y de agentes, y expresiones regulares de permitir y denegar.
    - Un interruptor por cada grupo de estadísticas de Redis. Todos están activados por defecto.

    ![Paso redis detailed del asistente con hilos, prefijos y filtros de expresiones regulares](../assets/images/discovery/redis/redis-task-detailed-options.png)

    ![Paso redis detailed del asistente con los interruptores de escaneo](../assets/images/discovery/redis/redis-task-scan-options.png)

3. **redis custom**: **umbrales** opcionales para los módulos creados y **consultas personalizadas**.

    ![Paso redis custom del asistente con la definición de umbrales](../assets/images/discovery/redis/redis-task-thresholds.png)

    ![Paso redis custom del asistente con la definición de consultas personalizadas](../assets/images/discovery/redis/redis-task-custom-queries.png)

El grupo y el intervalo de la tarea provienen del paso genérico de definición de la tarea. Se convierten en el grupo y el intervalo de los agentes creados.

### Cadenas de conexión

Escribe una conexión por línea, como pares `clave=valor` separados por comas. Añade `|` seguido de un nombre para elegir el nombre del agente:

```
host='<REDIS_HOST_1>', port=6379|<AGENT_NAME>
host='<REDIS_HOST_2>', port=6379
```

- Las comillas alrededor de los valores de texto son opcionales y se eliminan. `true` y `false` se leen como booleanos y los números enteros como números.
- Los pares se pasan a la conexión tal cual y el addon no los valida. Los ejemplos incluidos usan solo `host` y `port`.
- No uses una coma dentro de un valor, porque la coma separa los pares.
- **Nombre del agente**: si la línea no tiene sufijo `| <nombre>`, el agente se llama `redis_<host>`, donde `<host>` es el valor de `host` (o `unknown` si la línea no tiene `host`). Dos instancias en el mismo host sin nombre explícito producirían el mismo agente. **Indica siempre un nombre explícito cuando varias instancias compartan host y mantén cada nombre único.**
- Las líneas vacías o que empiezan por `#` o `;` se ignoran.

Las cadenas de conexión pueden contener credenciales. Se almacenan en la definición de la tarea; restringe en consecuencia quién puede editar tareas de Discovery.

### Umbrales

Cada línea define los umbrales de un módulo, o de todos los módulos cuyo nombre coincida con una expresión regular:

```
<MODULE_NAME_OR_REGEXP> [<TYPE>] = <TAG> <VALUE>|<TAG> <VALUE>
```

- `<TYPE>` es `name` (nombre exacto del módulo) o `regexp` (expresión regular buscada en el nombre del módulo). Sin tipo se asume `name`.
- Cada par `<TAG> <VALUE>` son dos palabras separadas por un espacio; los pares se separan con `|`. Los ejemplos incluidos usan `min_warning` y `min_critical`.
- La coincidencia se hace contra el **nombre final del módulo, incluido el prefijo de módulos**. Con el prefijo `pre-`, la línea debe ser `pre-used_memory [name] = ...`.
- Solo se aplica la primera línea que coincide con un módulo.
- Las líneas que empiezan por `#` o `;` son comentarios. Cualquier otra línea debe contener `=`; de lo contrario toda la tarea falla con `Error while reading configuration file`.

```
pre-used_memory [name] = min_warning 75|min_critical 85
pre-used_cpu [regexp] = min_warning 50|min_critical 80
```

### Consultas personalizadas

Cada línea define un módulo cuyo valor procede de una consulta de búsqueda de Redis:

```
<MODULE_NAME>|<MODULE_TYPE>|<INDEX>|<QUERY>|<FIELD>
```

| Parte | Obligatoria | Descripción |
|-------|-------------|-------------|
| `<MODULE_NAME>` | Sí | Nombre del módulo. Se antepone el prefijo de módulos |
| `<MODULE_TYPE>` | Sí | Tipo de módulo de Pandora FMS, por ejemplo `generic_data_string`. Con `generic_data`, un valor que no es un número entero pasa a `generic_data_string` |
| `<INDEX>` | Sí | Nombre de un índice de búsqueda existente |
| `<QUERY>` | Sí | Consulta de búsqueda para ese índice |
| `<FIELD>` | No | Clave a extraer del documento resultante. Solo se aplica cuando la consulta devuelve exactamente un documento |

```
custom_module 1|generic_data_string|idx:users|Paul @age:[30 40]|name
custom_module 2|generic_data_string|idx:users|@city:{Tel Aviv}
```

- Una línea con menos de cuatro partes se omite sin aviso, y una línea no puede contener `|` dentro de la consulta.
- Si la consulta devuelve varios documentos, el valor son los documentos como texto, uno por línea, y `<FIELD>` se ignora. Si no devuelve ninguno, el valor es vacío.
- Las consultas personalizadas crean un módulo por consulta en **cada** agente de la tarea y no les afectan las expresiones de permitir y denegar.
- Una consulta que falla se notifica en la información de ejecución como `[ERROR] Query '<MODULE_NAME>' failed`.

## Verificar la primera ejecución

Fuerza la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea.** Una tarea completada informa de **Total agents**, el número de agentes que ha creado.

    ![Resumen de la tarea de Discovery con el contador Total agents](../assets/images/discovery/redis/redis-task-summary.png)

2. **La información de ejecución.** Aquí aparecen las conexiones y consultas fallidas, por ejemplo `[<AGENT_NAME>] Connection failed.` Un fallo de conexión no detiene a las demás instancias.
3. **Los agentes.** Uno por cadena de conexión, con el nombre descrito en [Cadenas de conexión](#cadenas-de-conexion).
4. **Los módulos.** Busca `uptime_in_seconds` (servidor), `connected_clients` (clientes) y `used_memory` (memoria), según los interruptores activados.

## Entender los resultados

### Agentes y módulos generados

- **Agente**: uno por cadena de conexión. El alias es el prefijo de agentes más el nombre del agente; el nombre interno del agente se deriva de ese alias, de modo que cambiar el prefijo o el nombre crea un agente nuevo.
- **Módulos**: uno por cada estadística que devuelve Redis, con nombre `<prefijo de módulos><estadística>`, más uno por cada consulta personalizada. Una estadística numérica se convierte en un módulo `generic_data` y cualquier otra en `generic_data_string`.
- **No se crean**: una estadística con valor `0`, vacío o una lista no genera módulo. Un contador que vale `0` en la primera ejecución aparece cuando tiene valor por primera vez.
- **Filtros**: las expresiones de permitir y denegar se aplican al nombre de la estadística **sin** el prefijo de módulos. Primero se evalúa la expresión de permitir y después la de denegar.
- Un grupo de estadísticas solo se lee si su interruptor **Scan** está activado, y el conjunto de estadísticas de cada grupo depende de la versión de Redis y de los módulos cargados en ella.

### Grupos de estadísticas

| Interruptor | Qué lee |
|-------------|---------|
| Scan server stats | Identidad del servidor, proceso y tiempo en marcha |
| Scan clients stats | Clientes conectados, bloqueados y de seguimiento, y límites de clientes |
| Scan memory stats | Uso de memoria, picos, fragmentación, asignador y política de expulsión |
| Scan persistance stats | Estado de las instantáneas y del archivo de solo anexado |
| Scan threads stats | Información de hilos |
| Scan stats | Conexiones, comandos, tráfico de red, expiraciones, expulsiones y contadores de aciertos y fallos |
| Scan replication stats | Rol, réplicas y backlog de replicación |
| Scan CPU stats | Tiempo de CPU del servidor y de sus procesos hijos |
| Scan command stats | Llamadas y tiempo de cada comando ejecutado (`cmdstat_<comando>`) |
| Scan latency stats | Percentiles de latencia de cada comando ejecutado |
| Scan sentinel stats | Información de Sentinel |
| Scan cluster stats | Si el modo clúster está activado |
| Scan modules stats | Módulos cargados y, con el módulo de búsqueda, estadísticas de índices (`search_*`) |
| Scan keyspace stats | Una entrada por base de datos (`db0`, `db1`, ...) |
| Scan error stats | Contadores de errores (`errorstat_<error>`) |

La entrada del Marketplace lista los nombres de estadísticas que produce cada grupo en una ejecución de referencia. Un grupo puede contener menos o más estadísticas según tu versión de Redis. Las estadísticas de comandos, latencia, keyspace y errores llevan el nombre del comando, la base de datos o el error en el nombre del módulo, y su valor es un compuesto de varias cifras.

<!-- SCREENSHOT NEEDED: Vista de un agente de Redis creado por la tarea con módulos representativos como used_memory, connected_clients y uptime_in_seconds, solo con nombres de host de laboratorio. -->

## Operar

El addon puede ejecutarse a mano con el archivo de configuración que construye la tarea de Discovery. Es la forma más rápida de probar conexiones, consultas y umbrales sin una tarea de Discovery.

```bash
./pandora_redis --conf <PATH_TO_CONFIG>
```

`--conf` es el único parámetro y es obligatorio. La ejecución imprime el resumen de Discovery (incluido **Total agents**) y envía los datos de los agentes con Tentacle.

```ini
[CONF]
threads = 1
prefix = pre-
prefix_agents =
agents_group = <GROUP_ID>
interval = 300
tentacle_ip = <TENTACLE_SERVER_IP>
tentacle_port = 41121
allow_regexp =
deny_regexp =
scan_server = 1
scan_clients = 1
scan_memory = 1

[CONNECTION_STRINGS]
host='<REDIS_HOST_1>', port=6379
host='<REDIS_HOST_2>', port=6379|<AGENT_NAME>

[THRESHOLDS]
pre-used_memory [name] = min_warning 75|min_critical 85

[QUERIES]
custom_module 1|generic_data_string|idx:users|Paul @age:[30 40]|name
```

- La sección es `[THRESHOLDS]`. Una sección llamada `[UMBRALS]` se ignora.
- Una clave `scan_*` omitida está activada. Ponla a `0` para desactivarla.
- Las credenciales de un archivo de configuración necesitan la misma protección que la definición de la tarea. Restringe los permisos del archivo.

**Paralelismo**: **Max threads** limita cuántas instancias de Redis se procesan a la vez. Un valor mayor acorta la ejecución y aumenta el uso de CPU del servidor de Discovery.

## Solucionar problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es la información de ejecución de la tarea.

| Síntoma o mensaje | Causa y acción |
|-------------------|----------------|
| `[<AGENT_NAME>] Connection failed.` | La instancia no respondió a `PING`. Comprueba host, puerto, ruta de red y credenciales desde el servidor de Discovery. Una instancia fallida no crea agente |
| `[ERROR] Can't create client` / `[ERROR] Can't obtain data` | No se pudo usar la cadena de conexión o no se pudo leer la información. Revisa la sintaxis y que el usuario pueda ejecutar `INFO` |
| `Error while reading configuration file` | Una línea de umbrales no tiene `=`, o hay otra línea mal formada en el archivo generado. Corrige los umbrales |
| `[WARNING] The defined thresholds could not be parsed. Please check your syntax.` | El bloque de umbrales se ignoró. Revisa el formato |
| `[WARNING] The defined queries could not be parsed. Please check your syntax.` | El bloque de consultas se ignoró. Revisa el formato |
| `[ERROR] Query '<MODULE_NAME>' failed: ...` | El índice no existe, la consulta no es válida o el usuario no puede ejecutar el comando de búsqueda |
| Una línea de consulta no produce módulo | Tiene menos de cuatro partes o está comentada |
| `Can't aplicate defined thresholds in modules. Check syntax` | No se pudieron aplicar los umbrales. Revisa la sintaxis |
| Los umbrales no se aplican | La línea no coincide con el nombre final del módulo, que incluye el prefijo de módulos |
| Dos instancias producen un solo agente | Comparten nombre. Da a cada cadena de conexión un `| <nombre>` único |
| Falta un módulo esperado | Su estadística vale `0` o está vacía, su grupo está desactivado o una expresión de permitir o denegar lo eliminó |
| `Tokens_dict must be a non-empty dictionary` | Todos los interruptores **Scan** están desactivados. Activa al menos uno |

## Referencia

### Parámetros de la tarea

#### Redis base

| Campo | Macro | Tipo | Obligatorio | Por defecto | Descripción |
|-------|-------|------|-------------|-------------|-------------|
| Connection strings | `_configConnections_` | textarea | Sí | Vacío | Una conexión por línea. Consulta [Cadenas de conexión](#cadenas-de-conexion) |
| Tentacle IP | `_tentacleIP_` | string | Sí | `127.0.0.1` | Servidor Tentacle que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | number | Sí | `41121` | Puerto del servidor Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | string | No | Vacío | Presente en la consola. Esta versión del addon no lo aplica |

#### redis detailed

| Campo | Macro | Tipo | Obligatorio | Por defecto | Descripción |
|-------|-------|------|-------------|-------------|-------------|
| Max threads | `_threads_` | number | No | `1` | Número máximo de instancias procesadas a la vez. Usa un número entero positivo |
| Use prefix for modules | `_usePrefixModules_` | checkbox | No | Desactivado | Muestra **Prefix for modules created** |
| Prefix for modules created | `_prefixModules_` | string | No | Vacío | Se antepone a cada nombre de módulo, incluidas las consultas personalizadas |
| Use prefix for agents | `_usePrefixAgents_` | checkbox | No | Desactivado | Muestra **Prefix for agents created** |
| Prefix for agents created | `_prefixAgents_` | string | No | Vacío | Se antepone a cada nombre de agente |
| Regexp to filter modules | `_regexpFilter_` | checkbox | No | Desactivado | Muestra **Allow regexp** |
| Allow regexp | `_allowRegexp_` | string | No | Vacío | Solo se crean las estadísticas cuyo nombre coincide |
| Regexp to discard modules | `_regexpDiscard_` | checkbox | No | Desactivado | Muestra **Deny regexp** |
| Deny regexp | `_denyRegexp_` | string | No | Vacío | No se crean las estadísticas cuyo nombre coincide |
| Scan server stats | `_checkServer_` | checkbox | No | Activado | Clave de configuración `scan_server` |
| Scan clients stats | `_checkClients_` | checkbox | No | Activado | `scan_clients` |
| Scan memory stats | `_checkMemory_` | checkbox | No | Activado | `scan_memory` |
| Scan persistance stats | `_checkPersistance_` | checkbox | No | Activado | `scan_persistence` |
| Scan threads stats | `_checkThreads_` | checkbox | No | Activado | `scan_threads` |
| Scan stats | `_checkStats_` | checkbox | No | Activado | `scan_stats` |
| Scan replication stats | `_checkReplication_` | checkbox | No | Activado | `scan_replication` |
| Scan CPU stats | `_checkCpu_` | checkbox | No | Activado | `scan_cpu` |
| Scan command stats | `_checkCommandStats_` | checkbox | No | Activado | `scan_commandstats` |
| Scan latency stats | `_checkLatencyStats_` | checkbox | No | Activado | `scan_latencystats` |
| Scan sentinel stats | `_checkSentinel_` | checkbox | No | Activado | `scan_sentinel` |
| Scan cluster stats | `_checkCluster_` | checkbox | No | Activado | `scan_cluster` |
| Scan modules stats | `_checkModules_` | checkbox | No | Activado | `scan_modules` |
| Scan keyspace stats | `_checkKeyspace_` | checkbox | No | Activado | `scan_keyspace` |
| Scan error stats | `_checkErrorStats_` | checkbox | No | Activado | `scan_errorstats` |

#### redis custom

| Campo | Macro | Tipo | Obligatorio | Por defecto | Descripción |
|-------|-------|------|-------------|-------------|-------------|
| Define tresholds | `_configTresholds_` | textarea | No | Ejemplos comentados | Consulta [Umbrales](#umbrales) |
| Custom queries | `_configQueries_` | textarea | No | Ejemplos comentados | Consulta [Consultas personalizadas](#consultas-personalizadas) |

### Parámetros de línea de comandos

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `--conf` | Sí | Ruta al archivo de configuración |

### Archivo de configuración

| Sección | Clave | Valor si se omite | Descripción |
|---------|-------|-------------------|-------------|
| `[CONF]` | `threads` | `4` | Instancias procesadas a la vez |
| `[CONF]` | `prefix` | Vacío | Prefijo de nombres de módulo |
| `[CONF]` | `prefix_agents` | Vacío | Prefijo de nombres de agente |
| `[CONF]` | `agents_group` | Vacío | Id del grupo de los agentes creados |
| `[CONF]` | `interval` | `300` | Intervalo de los agentes creados, en segundos |
| `[CONF]` | `transfer_mode` | `tentacle` | Modo de transferencia de datos. La tarea de Discovery usa siempre `tentacle` |
| `[CONF]` | `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `[CONF]` | `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `[CONF]` | `allow_regexp` | Vacío | Expresión de permitir |
| `[CONF]` | `deny_regexp` | Vacío | Expresión de denegar |
| `[CONF]` | `scan_server`, `scan_clients`, `scan_memory`, `scan_persistence`, `scan_threads`, `scan_stats`, `scan_replication`, `scan_cpu`, `scan_commandstats`, `scan_latencystats`, `scan_sentinel`, `scan_cluster`, `scan_modules`, `scan_keyspace`, `scan_errorstats` | `1` | `1` lee el grupo, `0` lo omite |
| `[CONNECTION_STRINGS]` | — | — | Una conexión por línea |
| `[THRESHOLDS]` | — | — | Una definición de umbral por línea |
| `[QUERIES]` | — | — | Una consulta personalizada por línea |

### Identidad del addon

| Campo | Valor |
|-------|-------|
| Nombre corto de la app | `pandorafms.redis` |
| Versión del addon | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
| Marketplace | Descarga limitada a usuarios con licencia |
