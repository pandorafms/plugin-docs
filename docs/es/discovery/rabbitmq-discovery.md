# RabbitMQ Discovery

*Última actualización del artículo: 2026-10-01.*

## Qué monitoriza

El plugin de Discovery de RabbitMQ se conecta a uno o varios brokers de RabbitMQ a través de su Management API y convierte el estado y el rendimiento del clúster en agentes y módulos de Pandora FMS. Lee una lista de objetivos dados como URL de la Management API, se autentica con HTTP Basic y recoge datos de clúster, nodos, exchanges, conexiones, colas, canales y hosts virtuales mediante los endpoints de lectura de la API.

Una tarea de Discovery crea un agente por objetivo. Cada grupo de métricas es opcional y se controla desde la tarea, por lo que el mismo plugin puede recoger solo el resumen del clúster o el inventario completo de colas, canales y hosts virtuales.

Una extensión de consola complementaria, **RabbitMQ Dashboard**, presenta los agentes y módulos generados en una única vista de monitorización.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.rabbitmq.discovery`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| Un endpoint de la Management API de RabbitMQ alcanzable | `Requerido` | El plugin establece conexiones remotas con cada objetivo y consulta sus endpoints `/api`. Prerrequisito, no una declaración de compatibilidad. |
| El plugin de gestión de RabbitMQ habilitado en cada broker | `Requerido` | Los datos recogidos los sirve la Management API. Sin él los endpoints no están disponibles. Prerrequisito, no una declaración de compatibilidad. |
| Un usuario de RabbitMQ con acceso de lectura a la Management API | `Requerido` | El plugin se autentica con HTTP Basic en cada petición. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a RabbitMQ](#preparar-el-acceso-a-rabbitmq). |
| Una versión concreta de RabbitMQ | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión concreta de RabbitMQ. |
| Una versión concreta de Pandora FMS | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión de consola o de servidor. |
| Un sistema operativo concreto del host | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con sistemas operativos para la máquina que ejecuta el plugin. |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **El plugin de gestión de RabbitMQ habilitado** en cada broker a monitorizar, para que se sirva la Management API.
3. **Conectividad** entre el servidor de Pandora FMS y la Management API de cada broker (puerto por defecto `15672` para HTTP, `443` para HTTPS).
4. **Un usuario de RabbitMQ con acceso de lectura a la Management API.** Consulte [Preparar el acceso a RabbitMQ](#preparar-el-acceso-a-rabbitmq).
5. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados, tomados de la tarea de Discovery.

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) con sus dependencias de Python empaquetadas, por lo que no es necesario instalar librerías de Python adicionales en el servidor de Discovery.

### Preparar el acceso a RabbitMQ

El plugin se autentica contra la Management API con HTTP Basic y solo realiza peticiones de lectura (`GET`), por lo que la cuenta solo necesita acceso a los endpoints que consulta la tarea.

- **Habilite el plugin de gestión** en cada broker y confirme que la Management API responde, por ejemplo `https://<TARGET_HOST>:15672/api/overview`.
- **Cree un usuario dedicado** y concédale los privilegios mínimos que permitan leer la Management API de los hosts virtuales monitorizados. No se necesita acceso de escritura.
- **Prefiera HTTPS.** Sobre HTTP simple las credenciales Basic viajan sin cifrar. Para usar HTTPS con una autoridad de certificación privada, indique en **CA file** el conjunto PEM del servidor de Pandora.

El plugin nunca publica, consume ni modifica recursos de RabbitMQ; solo lee la API.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager** (la vista *Manage disco packages*). Una vez cargado, **RabbitMQ** aparece en la categoría **Applications** del asistente de Discovery.

La extensión complementaria **RabbitMQ Dashboard** es una extensión de consola. Instálela como paquete de extensión de consola; una vez instalada añade la entrada **RabbitMQ Dashboard** al menú **Monitoring**. Requiere que existan los agentes generados por este plugin.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → RabbitMQ**. El primer paso genérico define la tarea; el paquete añade **Connection**, **Agents and filters** y **Metrics and module filters**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El ID del grupo y el intervalo se pasan al plugin y se aplican a todos los agentes generados.

**Paso 2 — Connection.** Los objetivos a los que conectarse y cómo se alcanza la API:

- **Targets** es la lista de URL de la Management API, una por línea o separadas por comas. Cada entrada es una URL simple, por ejemplo `http://172.17.0.2:15672`, o un objeto JSON con `url`, `user`, `password` y `alias`. Las líneas que empiezan por `#` son comentarios. Consulte [Archivo de objetivos](#archivo-de-objetivos).
- **Default user** y **Default password** se aplican a los objetivos que no llevan sus propias credenciales en línea, y a los objetivos con URL simple.
- **Request timeout seconds** y **HTTP retries** ajustan cómo se llama a la API.
- **Verify TLS certificates** valida los certificados y los nombres de host HTTPS, y **CA file** apunta a un conjunto PEM opcional en el servidor de Pandora.

![Paso Connection de la tarea de Discovery de RabbitMQ: objetivos, credenciales y opciones TLS.](../assets/images/discovery/rabbitmq-discovery/connection-step.png)

**Paso 3 — Agents and filters.** Nombres de los agentes y filtros de recursos:

- **Agent alias prefix** se antepone al alias visible del agente. No afecta a la identidad del agente.
- **Module prefix** se antepone a todos los nombres de módulo generados.
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos.
- **Queue name regexp** y **Vhost name regexp** restringen qué colas, exchanges y hosts virtuales se recogen. Vacío coincide con todo.

![Paso Agents and filters de la tarea de Discovery de RabbitMQ.](../assets/images/discovery/rabbitmq-discovery/agents-filters-step.png)

**Paso 4 — Metrics and module filters.** Qué grupos de métricas se recogen y qué módulos se conservan:

- Los doce conmutadores habilitan el resumen del clúster, las tasas globales de mensajes, las métricas y recursos de los nodos, los contadores IO de los nodos, las métricas y tasas de las colas, los exchanges, el resumen de conexiones y el detalle por conexión, los canales y los hosts virtuales.
- **Modules allow regexp** y **Modules deny regexp** filtran los nombres finales de los módulos. La lista de denegación tiene prioridad sobre la de permisión.

![Paso Metrics and module filters de la tarea de Discovery de RabbitMQ.](../assets/images/discovery/rabbitmq-discovery/metrics-step.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de `resources_discovered`, `resources_vanished`, `modules` y `errors`. `resources_discovered` es el número de objetivos alcanzables; `errors` cuenta los endpoints de la API que fallaron durante la ejecución. El ejemplo siguiente muestra un único objetivo descubierto con `141` módulos y sin errores.

2. **El agente.** Aparece un agente por objetivo alcanzable, llamado `rabbitmq-<identificador>` con el alias tomado de la URL del objetivo o de su `alias`. Un objetivo inalcanzable no produce agente y se informa en la información de ejecución.

3. **Los módulos.** El agente lleva el módulo `Availability` más los grupos de métricas habilitados en el paso 4, según lo que reporte el broker.

![Resumen de ejecución de una tarea de Discovery de RabbitMQ.](../assets/images/discovery/rabbitmq-discovery/task-summary.png)

El detalle del agente lista los módulos generados con su valor actual, estado y descripción.

![Agente de Discovery de RabbitMQ con sus módulos generados.](../assets/images/discovery/rabbitmq-discovery/agent-modules.png)

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por objetivo. El nombre del agente es `rabbitmq-` seguido de un identificador de 32 caracteres derivado de la tarea y de la URL normalizada del objetivo, por lo que el nombre es estable entre ejecuciones para la misma tarea y objetivo. El alias es el alias del objetivo cuando se indica, o la URL del objetivo, con **Agent alias prefix** antepuesto.

Cada agente generado informa de `Other` como sistema operativo, pertenece al grupo de la tarea (por ID) con el intervalo de la tarea y lleva la dirección base del objetivo. Se marca con el valor `extra_data` de nivel de agente `rabbitmq:agent:<identificador>`, que permite a la consola y al panel complementario identificarlo como agente de Discovery de RabbitMQ. Con **Agent autodisable mode** habilitado los agentes se crean en el modo `2` de Pandora FMS.

Los objetivos se agrupan por su URL normalizada; las URL normalizadas duplicadas se rechazan. Los objetivos que no llevan credenciales en línea usan **Default user** y **Default password** de la tarea.

### Módulos por agente

Todos los módulos se crean en el agente objetivo; el nombre del recurso se añade al nombre del módulo para que un solo agente pueda contener todos los nodos, colas, canales o hosts virtuales. Los sufijos de recurso son `<etiqueta> - <nodo>` para los nodos, `<etiqueta> - channel <nombre>` para los canales, `<etiqueta> - vhost <nombre>` para los hosts virtuales, `<etiqueta> - connection <nombre>` para las conexiones, y `<etiqueta> - ["<vhost>","<nombre>"]` para colas y exchanges.

| Conmutador | Módulos que añade |
| --- | --- |
| **Overview modules** | Nombre del clúster, versión de RabbitMQ, totales de mensajes y totales de objetos |
| **Global message rates** | Tasas globales de publish, deliver, get, ack, confirm y relacionadas |
| **Node modules** | Estado, memoria y métricas de procesos Erlang por nodo |
| **Node resource modules** | Límites, alarmas, descriptores, sockets, tiempo de actividad y run queue por nodo |
| **Node IO counters** | Contadores de operaciones, bytes y recolección de basura por nodo |
| **Queue modules** | Mensajes, consumidores, memoria, estado y tipo por cola |
| **Queue message rates** | Tasas de publish, deliver, ack y redeliver por cola |
| **Exchange modules** | Tasas agregadas de exchanges y tasas publish in/out por exchange |
| **Connection summary** | Totales de conexiones y tasas de red agregadas |
| **Per connection modules** | Canales, tasas de red y estado por conexión |
| **Channel modules** | Consumidores, contadores y tasas por canal |
| **Vhost modules** | Totales de mensajes y tasas por host virtual |

Los nombres de módulo son `<Module prefix>` más el nombre del módulo. El inventario exhaustivo y el campo exacto de la API detrás de cada módulo están en [Módulos y agentes generados](#modulos-y-agentes-generados).

### RabbitMQ Dashboard

**RabbitMQ Dashboard** es una extensión de consola complementaria que lee los agentes marcados con `rabbitmq:agent:` (y, como alternativa, los agentes llamados `rabbitmq-`) y sus módulos habilitados, y los presenta en una única vista. Aparece en el menú **Monitoring** y requiere el permiso estándar de lectura de agentes.

El panel tiene tres filtros: **Target** (un agente o todos), **Section** (una sección o todas) y **Chart period** para el gráfico de histórico. Las secciones disponibles son **Overview**, **Message rates**, **Nodes**, **Exchanges**, **Connections**, **Queues**, **Channels**, **Vhosts** y **History**.

- **Overview** muestra los KPI del clúster, el backlog de mensajes (ready frente a unacknowledged) y los totales de objetos. **Message rates** representa las tasas globales que reporta el endpoint de resumen.

![Vista Overview y tasas globales de mensajes del RabbitMQ Dashboard.](../assets/images/discovery/rabbitmq-discovery/dashboard-overview.png)

- **Nodes** lista cada nodo con su estado, memoria, procesos, disco, descriptores, sockets, tiempo de actividad, run queue y alarmas. **Exchanges** lista las tasas de publish in/out y los exchanges más activos.

![Nodos y exchanges del RabbitMQ Dashboard.](../assets/images/discovery/rabbitmq-discovery/dashboard-nodes-exchanges.png)

- **Connections** muestra el resumen de conexiones, el desglose por estado y el detalle por conexión. **Queues** lista cada cola con su estado, backlog, consumidores, memoria y tipo.

![Conexiones y colas del RabbitMQ Dashboard.](../assets/images/discovery/rabbitmq-discovery/dashboard-connections-queues.png)

- **Channels** y **Vhosts** listan los consumidores y tasas de mensajes por recurso. **History** representa los contadores clave durante el periodo seleccionado.

![Colas, canales, hosts virtuales e histórico del RabbitMQ Dashboard.](../assets/images/discovery/rabbitmq-discovery/dashboard-queues-channels.png)

Cuando no se encuentra ningún agente de RabbitMQ, el panel muestra el mensaje *No RabbitMQ data found* con la indicación de ejecutar la tarea de Discovery y comprobar que se crearon los agentes y módulos.

## Operación

### Ejecución manual

El plugin puede ejecutarse fuera de Discovery, desde un agente de Pandora FMS o directamente desde la línea de comandos, con un archivo de configuración, un archivo de objetivos y los archivos opcionales de filtros de módulos:

```bash
./pandora_rabbitmq --conf <PATH_TO_CONFIG> --targets-file <PATH_TO_TARGETS> --module-allow-list-file <PATH_TO_ALLOW> --module-deny-list-file <PATH_TO_DENY>
```

Solo `--conf` y `--targets-file` son obligatorios. El plugin lee cada objetivo, recoge los grupos de métricas habilitados e imprime en la salida estándar la salida JSON de Discovery con los agentes y módulos. Consulte [Archivo de configuración](#archivo-de-configuracion) y [Ejecución en línea de comandos](#ejecucion-en-linea-de-comandos).

El archivo de objetivos puede embeber un nombre de usuario y una contraseña. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalo fuera de directorios compartidos, registros y control de versiones. Cuando las credenciales viajan en argumentos de comando, el historial del shell y la lista de procesos pueden exponerlas; prefiera el archivo de configuración.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente y la información de ejecución registra un error de conexión o de tiempo de espera | Confirme que el broker es alcanzable desde el servidor de Pandora FMS por el puerto de su Management API (por defecto `15672` para HTTP), que el plugin de gestión está habilitado y que la URL del objetivo es correcta. |
| La información de ejecución registra `HTTP 401` | El usuario o la contraseña son incorrectos, o el usuario no puede leer la Management API. Revise **Default user** y **Default password**, y las credenciales en línea del objetivo. |
| La información de ejecución registra `HTTP 404` | La URL no apunta a la Management API del broker. Compruebe el host y el puerto y elimine cualquier sufijo `/api`, que el plugin recorta automáticamente. |
| Errores de certificado TLS | Indique en **CA file** el conjunto PEM que firma el certificado del broker, o deshabilite **Verify TLS certificates** solo en entornos de prueba de confianza. |
| El inventario de colas o de hosts virtuales está vacío mientras el resumen del clúster funciona | Habilite **Queue modules**, **Queue message rates**, **Channel modules** o **Vhost modules**, y revise **Queue name regexp** y **Vhost name regexp**: un valor vacío coincide con todo, una expresión que no coincide no conserva nada. |
| Faltan módulos esperados | Revise los conmutadores de **Metrics and module filters** y los filtros **Modules allow regexp** / **Modules deny regexp**. La lista de denegación se aplica después de la de permisión. |
| El panel muestra *No RabbitMQ data found* | Ejecute la tarea de Discovery y confirme que el plugin creó agentes marcados `rabbitmq:agent:` (o llamados `rabbitmq-`) y que la cuenta de consola puede leerlos. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Connection

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Targets | `_targets_` | textarea | — | URL de la Management API, una por línea o separadas por comas, u objetos JSON de objetivo. Obligatorio |
| Default user | `_user_` | string | — | Usuario para los objetivos sin credenciales propias. Todo objetivo necesita un usuario |
| Default password | `_password_` | password | — | Contraseña para los objetivos sin credenciales propias |
| Request timeout seconds | `_timeout_` | string | `10` | Tiempo de espera de cada petición HTTP. Debe ser positivo |
| HTTP retries | `_retries_` | string | `2` | Reintentos ante errores HTTP transitorios, entre `0` y `5` |
| Verify TLS certificates | `_verifytls_` | checkbox | on | Valida los certificados y nombres de host HTTPS |
| CA file | `_cafile_` | string | — | Conjunto PEM de CA opcional en el servidor de Pandora, usado en objetivos HTTPS |

#### Agents and filters

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Agent alias prefix | `_agentprefix_` | string | — | Prefijo del alias visible; la identidad del agente no cambia |
| Module prefix | `_moduleprefix_` | string | — | Prefijo de todos los nombres de módulo generados |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` de Pandora FMS |
| Queue name regexp | `_queuefilter_` | string | — | Filtro de nombres de cola. Vacío coincide con todo |
| Vhost name regexp | `_vhostfilter_` | string | — | Filtro de hosts virtuales para colas, exchanges y vhosts. Vacío coincide con todo |

#### Metrics and module filters

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Overview modules | `_overviewenabled_` | checkbox | on | Nombre del clúster, versión, totales de mensajes y totales de objetos |
| Global message rates | `_messageratesenabled_` | checkbox | on | Tasas globales de publish, deliver, get, ack, confirm y relacionadas |
| Node modules | `_nodesenabled_` | checkbox | on | Estado, memoria y métricas de procesos Erlang del nodo |
| Node resource modules | `_noderesourcesenabled_` | checkbox | on | Límites, alarmas, descriptores, sockets, tiempo de actividad y run queue |
| Node IO counters | `_nodeioenabled_` | checkbox | off | Contadores de operaciones, bytes y recolección de basura |
| Queue modules | `_queuesenabled_` | checkbox | off | Mensajes, consumidores, memoria, estado y tipo por cola |
| Queue message rates | `_queueratesenabled_` | checkbox | off | Tasas de publish, deliver, ack y redeliver por cola |
| Exchange modules | `_exchangesenabled_` | checkbox | on | Tasas agregadas y por exchange |
| Connection summary | `_connectionsenabled_` | checkbox | on | Totales de conexiones y tasas de red agregadas |
| Per connection modules | `_connectiondetailsenabled_` | checkbox | off | Canales, tasas de red y estado por conexión |
| Channel modules | `_channelsenabled_` | checkbox | off | Consumidores, contadores y tasas por canal |
| Vhost modules | `_vhostsenabled_` | checkbox | off | Totales de mensajes y tasas por host virtual |
| Modules allow regexp | `_moduleallowlist_` | textarea | — | Una expresión regular por línea. Coincide con los nombres finales de módulo |
| Modules deny regexp | `_moduledenylist_` | textarea | — | Una expresión regular por línea. La denegación tiene prioridad sobre la permisión |

### Archivo de configuración

La tarea de Discovery construye un archivo `--conf` temporal a partir de sus propios campos. Una ejecución manual lo suministra directamente. El archivo tiene una sección `[CONF]`; un archivo sin cabecera de sección se lee como si la tuviera.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `user` | Vacío | Usuario por defecto para los objetivos sin credenciales propias |
| `pass` | Vacío | Contraseña por defecto para los objetivos sin credenciales propias |
| `timeout` | `10` | Tiempo de espera de cada petición HTTP, en segundos |
| `retries` | `2` | Reintentos ante errores HTTP transitorios, entre `0` y `5` |
| `verify_tls` | `1` | Valida los certificados y nombres de host HTTPS |
| `ca_file` | Vacío | Conjunto PEM de CA usado en objetivos HTTPS |
| `task_id` | — | Identificador de la tarea; se usa para derivar el nombre estable del agente. Obligatorio |
| `group_id` | `0` | ID del grupo donde se crean los agentes. Debe ser positivo |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes |
| `agent_prefix` | Vacío | Prefijo del alias visible del agente |
| `module_prefix` | Vacío | Prefijo de todos los nombres de módulo |
| `agent_autodisable` | `0` | Crea los agentes en el modo `2` de Pandora FMS cuando está habilitado |
| `queue_filter` | Vacío | Expresión regular de nombres de cola |
| `vhost_filter` | Vacío | Expresión regular de vhost para colas, exchanges y vhosts |
| `overview_enabled` | `1` | Habilita los módulos de resumen |
| `message_rates_enabled` | `1` | Habilita las tasas globales de mensajes |
| `nodes_enabled` | `1` | Habilita los módulos de nodo |
| `node_resources_enabled` | `1` | Habilita los módulos de recursos de nodo |
| `node_io_enabled` | `0` | Habilita los contadores IO de nodo |
| `queues_enabled` | `0` | Habilita los módulos de cola |
| `queue_rates_enabled` | `0` | Habilita las tasas de mensajes de cola |
| `exchanges_enabled` | `1` | Habilita los módulos de exchange |
| `connections_enabled` | `1` | Habilita el resumen de conexiones |
| `connection_details_enabled` | `0` | Habilita los módulos por conexión |
| `channels_enabled` | `0` | Habilita los módulos de canal |
| `vhosts_enabled` | `0` | Habilita los módulos de vhost |
| `module_allow_list` | Vacío | Expresiones regulares de permisión en línea, una por línea |
| `module_deny_list` | Vacío | Expresiones regulares de denegación en línea, una por línea |

### Archivo de objetivos

El archivo `--targets-file` contiene los objetivos. Acepta un array JSON de objetos de objetivo:

```json
[
  {"url": "http://172.17.0.2:15672", "user": "monitor", "password": "<PASSWORD>", "alias": "RabbitMQ lab"},
  {"url": "https://rabbitmq-prod.internal.company.com", "user": "monitor", "password": "<PASSWORD>"}
]
```

o una lista simple separada por comas o líneas, ignorando las líneas que empiezan por `#`:

```text
# Clúster de producción
http://172.17.0.2:15672
https://rabbitmq-prod.internal.company.com
```

Cada URL se normaliza antes de usarse: se asume `http://` cuando falta el esquema, el puerto por defecto es `443` para HTTPS y `15672` para HTTP, se elimina un `/api` final y se rechazan las credenciales embebidas, las cadenas de consulta y los fragmentos. Las URL normalizadas duplicadas se rechazan, y todo objetivo necesita un usuario, en línea o por defecto.

### Archivos de filtros de módulos

`--module-allow-list-file` y `--module-deny-list-file` contienen una expresión regular por línea, que se compara con los nombres finales de los módulos (después del prefijo de módulo). Un módulo se conserva cuando coincide con la lista de permisión (o la lista está vacía) y no coincide con la de denegación. Las mismas expresiones pueden suministrarse en línea mediante las claves de configuración `module_allow_list` y `module_deny_list`.

### Ejecución en línea de comandos

```bash
./pandora_rabbitmq --conf <PATH_TO_CONFIG> --targets-file <PATH_TO_TARGETS> --module-allow-list-file <PATH_TO_ALLOW> --module-deny-list-file <PATH_TO_DENY>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta al archivo de configuración. Obligatorio en Discovery |
| `--targets-file` | Ruta al archivo con los objetivos |
| `--module-allow-list-file` | Ruta al archivo con las expresiones regulares de permisión |
| `--module-deny-list-file` | Ruta al archivo con las expresiones regulares de denegación |
| `--host` | URL de un único objetivo, usada cuando no se da archivo de objetivos |
| `--user`, `--pass` | Credenciales por defecto |
| `--group-id`, `--interval` | ID de grupo e intervalo de los agentes generados |
| `--task-id` | Identificador de la tarea usado para derivar el nombre del agente |
| `--timeout`, `--retries`, `--ca-file` | Opciones HTTP y TLS |
| `--agent-prefix`, `--module-prefix` | Prefijos de alias y de módulo |
| `--version` | Imprime la versión del plugin |

Ejemplo de archivo de configuración:

```ini
[CONF]
user=monitor
pass=<PASSWORD>
timeout=10
retries=2
verify_tls=1
task_id=manual
group_id=10
interval=300
overview_enabled=1
message_rates_enabled=1
nodes_enabled=1
node_resources_enabled=1
exchanges_enabled=1
connections_enabled=1
```

### Módulos y agentes generados

Los nombres de módulo son `<Module prefix><nombre de módulo>`. Los módulos de recurso añaden ` - <recurso>` como se describe en [Módulos por agente](#modulos-por-agente).

**Agente objetivo** (uno por objetivo alcanzable)

Siempre se crea:

- `Availability`: `generic_proc`, `1` cuando se leyó el resumen del clúster, `0` en caso contrario.

Se crean cuando el conmutador correspondiente está habilitado:

- **Overview modules**: `Cluster name` y `RabbitMQ version` (`generic_data_string`), `Total queue messages`, `Messages ready`, `Messages unacknowledged`, `Overview connections`, `Total queues`, `Total exchanges`, `Total channels` y `Total consumers` (`generic_data`).
- **Global message rates** (por tasa): `Queue publish rate`, `Queue deliver get rate`, `Queue get rate`, `Queue deliver rate`, `Queue deliver no ack rate`, `Queue ack rate`, `Queue redeliver rate`, `Queue confirm rate`, `Queue return unroutable rate` y `Queue drop unroutable rate` (`generic_data`).
- **Node modules** (por nodo): `Node status` (`generic_proc`), `Memory used`, `Memory rate`, `Proc used` y `Proc details` (`generic_data`).
- **Node resource modules** (por nodo): `Memory limit`, `Disk free`, `Disk free limit`, `File descriptors used`, `File descriptors total`, `Sockets used`, `Sockets total`, `Proc total`, `Uptime ms` y `Run queue` (`generic_data`), y `Memory alarm` y `Disk alarm` (`generic_proc`).
- **Node IO counters** (por nodo): `Io read count`, `Io write count`, `Io read bytes`, `Io write bytes`, `Gc num` y `Gc bytes reclaimed` (`generic_data_inc`).
- **Queue modules** (por cola): `Messages`, `Messages ready`, `Messages unacknowledged`, `Consumers`, `Consumer capacity`, `Memory`, `Message bytes` y `Messages ram` (`generic_data`), y `State` y `Type` (`generic_data_string`).
- **Queue message rates** (por cola): `Queue publish rate`, `Queue deliver get rate`, `Queue ack rate` y `Queue redeliver rate` (`generic_data`).
- **Exchange modules**: `Exchanges in rate` y `Exchanges out rate` (`generic_data`), más `Exchange publish in rate` y `Exchange publish out rate` (`generic_data`) por exchange. Las tasas agregadas solo se crean cuando todos los exchanges reportan la tasa subyacente.
- **Connection summary**: `Total connections`, `Connections running`, `Connections blocked`, `Connections other`, `Total received octets rate` y `Total sent octets rate` (`generic_data`).
- **Per connection modules** (por conexión): `Channels`, `Received octets rate` y `Sent octets rate` (`generic_data`), y `State` (`generic_data_string`).
- **Channel modules** (por canal): `Consumers`, `Messages unacknowledged`, `Messages unconfirmed` y `Prefetch count` (`generic_data`), más `Channel publish rate`, `Channel deliver get rate`, `Channel ack rate` y `Channel redeliver rate` (`generic_data`).
- **Vhost modules** (por vhost): `Messages`, `Messages ready` y `Messages unacknowledged` (`generic_data`), más `Vhost publish rate`, `Vhost deliver get rate`, `Vhost ack rate` y `Vhost redeliver rate` (`generic_data`).

### Campos del agente

| Campo | Valor |
| --- | --- |
| Nombre del agente | `rabbitmq-<identificador>`, donde `<identificador>` se deriva de la tarea y de la URL normalizada del objetivo |
| Alias del agente | `<Agent alias prefix>` más el `alias` del objetivo, o la URL del objetivo |
| Sistema operativo | `Other` |
| Dirección | Nombre de host de la URL del objetivo |
| Grupo | El grupo de la tarea de Discovery, por ID |
| Intervalo | El intervalo de la tarea de Discovery |
| Modo de agente | `1`, o `2` cuando **Agent autodisable mode** está habilitado |
| `extra_data` | `rabbitmq:agent:<identificador>` |
| Descripción | `RabbitMQ Management API <URL del objetivo>` |

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.rabbitmq.discovery` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
| Extensión complementaria | RabbitMQ Dashboard |
