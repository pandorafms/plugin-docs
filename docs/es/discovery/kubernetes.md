# Kubernetes Discovery

*Última actualización del artículo: 2026-09-28.*

## Qué monitoriza

El plugin de Discovery de Kubernetes se conecta al servidor de API de Kubernetes de un clúster y descubre sus cargas de trabajo e infraestructura: nodos, pods, deployments, namespaces, servicios, estados de componentes y endpoints de salud de la API. Genera un agente de Pandora FMS por cada recurso descubierto y lo rellena con módulos de disponibilidad, capacidad y rendimiento leídos de la API.

El plugin genera agentes para:

- el propio clúster, mediante un agente global **Kubernetes**;
- cada nodo, cuando **Scan Nodes** está habilitado;
- cada deployment, cuando **Scan Deployments** está habilitado;
- cada pod ya planificado en un nodo, cuando **Scan Pods** está habilitado.

El agente global también lleva el estado de la API, los endpoints de salud, el número de servicios, el número de namespaces y los estados de componentes de todo el clúster.

El plugin se ejecuta como una tarea de Discovery: la consola crea la tarea, el servidor de Discovery ejecuta el plugin y los agentes y módulos generados se crean automáticamente. La tarea entrega los datos de los agentes generados a través de Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.3` (`pandorafms.kubernetes`) | Objetivo documentado | La versión que describe esta página, identificada por la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Un clúster de Kubernetes que exponga el servidor de API por HTTPS | `Requerido` | El plugin se conecta a `https://<host>:<port>` y lee los recursos de la API. Prerrequisito, no una declaración de compatibilidad |
| Un token Bearer que pueda leer los recursos de la API consultados | `Requerido` | El plugin se autentica con `Authorization: Bearer <token>` para listar nodos, pods, deployments, servicios, namespaces y estados de componentes. Prerrequisito, no una declaración de compatibilidad |
| La API de métricas de Kubernetes (`metrics.k8s.io`) para el uso de CPU y memoria | `Requerido` | Los módulos de CPU y memoria de nodos y contenedores se leen de `/apis/metrics.k8s.io/v1beta1`. Prerrequisito, no una declaración de compatibilidad |
| Una versión concreta de Kubernetes | `Sin validar` | Ningún registro de pruebas establece compatibilidad con una versión concreta de Kubernetes |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Un servidor de API de Kubernetes accesible desde el servidor de Discovery**, direccionado por host y puerto. El plugin usa siempre HTTPS; introduzca el host sin esquema.
3. **Un token Bearer** para el servidor de API. Es necesario para leer los endpoints protegidos; concédale acceso de lectura solo a los recursos que consulta la tarea. Las opciones **Scan API health checks** y **Scan component statuses** pueden necesitar permisos de API elevados, como indican las ayudas de la tarea.
4. **Un grupo de agentes y un intervalo de monitorización** para los agentes generados. Ambos vienen de la tarea de Discovery y los heredan todos los agentes generados.
5. **Accesibilidad de red hasta el destino de Tentacle**, porque la tarea transfiere los datos de los agentes generados a través de Tentacle.
6. El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que el servidor de Discovery ejecuta en el servidor de Pandora FMS.

El plugin usa siempre el esquema HTTPS y no verifica el certificado del servidor de API, por lo que funciona con certificados autofirmados, pero la conexión TLS no queda autenticada. El token Bearer se guarda en la configuración de la tarea; proteja la consola de Pandora FMS y su servidor conforme a su política de seguridad.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Kubernetes** aparece en la categoría **Applications** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Kubernetes**. El asistente recorre la definición genérica de la tarea y dos pasos del plugin: **Kubernetes base** y **Kubernetes detailed**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Task definition

El paso genérico pide el **nombre** de la tarea, el **grupo de agentes** y el **servidor** en el que se ejecuta, y el **intervalo**. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

### Paso 2 — Kubernetes base

Detalles de conexión y destino de Tentacle:

- **Kubernetes host** es la dirección o el nombre del servidor de API.
- **Kubernetes port** es el puerto del servidor de API.
- **Kubernetes token** es el token Bearer usado para autenticarse contra la API.
- **Use prefix** antepone un prefijo al nombre de cada agente generado; **Prefix** es ese prefijo.
- **Filter namespace** restringe el descubrimiento a un conjunto de namespaces, y **Namespace** es la lista de namespaces que se van a monitorizar.
- **Use proxy** enruta las peticiones a la API a través de un proxy; **Proxy url** es ese proxy.
- **Tentacle IP** y **Tentacle port** fijan el destino de Tentacle para los datos generados. Deje los valores por defecto salvo que su entorno necesite otro destino de Tentacle.

![Paso Kubernetes base](../assets/images/discovery/kubernetes/kubernetes-base.png)

### Paso 3 — Kubernetes detailed

Qué se escanea:

- **Scan Deployments**, **Scan Nodes** y **Scan Pods** habilitan o deshabilitan cada categoría de recurso.
- **Scan API health checks** genera los módulos de los endpoints de salud de la API. Los endpoints de salud pueden necesitar permisos de API elevados.
- **Scan component statuses** genera el recuento de componentes y los módulos de condiciones de componente. Los estados de componentes pueden necesitar permisos de API elevados.

![Paso Kubernetes detailed](../assets/images/discovery/kubernetes/kubernetes-detailed.png)

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** muestra el progreso general y un resumen con el número de agentes de nodo, de pod y de deployment generados, y el número total de agentes.
2. **Los agentes.** Espere el agente global **Kubernetes** más un agente por cada nodo, deployment y pod planificado descubiertos.
3. **Los módulos.** Cada agente generado lleva los módulos de su recurso; un clúster accesible con la API de métricas disponible rellena los valores de CPU y memoria.
4. **La información de ejecución.** Una ejecución correcta no informa de errores; cualquier fallo de petición concreto queda registrado ahí.

![Resumen de ejecución de la tarea](../assets/images/discovery/kubernetes/task-summary.png)

Si la tarea falla antes de generar nada, lo primero que hay que revisar son el host, el puerto, la accesibilidad de red y el token.

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por cada recurso descubierto. Los nombres de agente se construyen a partir del nombre original del recurso más el prefijo opcional.

| Agente | Nombre | Agente padre |
| --- | --- | --- |
| Global | `[Prefix]Kubernetes` | — |
| Nodo | `[Prefix]<nodo>` | El agente global |
| Deployment | `[Prefix]<deployment>` | El agente global |
| Pod | `[Prefix]<namespace>/<pod>` | El agente del nodo que ejecuta el pod |

Los agentes de deployment y de nodo son hijos del agente global Kubernetes; cada agente de pod es hijo del agente del nodo en el que se ejecuta y usa la IP del pod como dirección. El agente global se describe como `Kubernetes global agent`, los agentes de nodo como `Kubernetes node`, los de deployment como `Kubernetes deployment` y los de pod como `Kubernetes pod`.

Solo se descubren los pods ya planificados en un nodo: un pod sin nodo asignado se omite, igual que los recursos que la API devuelve sin nombre.

Cambiar **Prefix** más adelante cambia la identidad de todos los agentes generados. La opción **Filter namespace** se aplica solo a deployments y pods, porque los nodos tienen ámbito de clúster. La coincidencia de namespaces es exacta y distingue mayúsculas, y la lista se introduce como un array JSON, por ejemplo `["default","kube-system"]`. Cuando **Filter namespace** está habilitado, incluya al menos un namespace: una lista vacía no coincide con ninguna carga de trabajo y no se genera ningún agente de deployment ni de pod.

### Módulos por agente

Cada agente recibe los módulos de su recurso. Los valores se leen de la API en cada ejecución de la tarea; el nombre, el tipo y la unidad exactos de cada módulo están en [Módulos generados](#modulos-generados).

| Agente | Módulos que lleva |
| --- | --- |
| Global | Estado de la API, endpoints de salud de la API, número de servicios, número de namespaces, estados de componentes y número de deployments |
| Nodo | Uso de pods frente a la capacidad asignable del nodo, condiciones del nodo y, cuando la API de métricas está disponible, uso de CPU y memoria |
| Deployment | Recuentos de réplicas, preparación y disponibilidad del deployment |
| Pod | Fase y condiciones del pod, número de contenedores y, cuando la API de métricas está disponible, uso de CPU y memoria por contenedor |

![Módulos de un agente de pod generado](../assets/images/discovery/kubernetes/pod-modules.png)

## Operar

### Ejecución manual

El plugin también se puede ejecutar fuera del asistente de Discovery con un archivo de configuración. Resulta útil para probar la conectividad o para una ejecución puntual. Escriba un archivo de configuración con los pares `key=value` de [Claves del archivo de configuración](#claves-del-archivo-de-configuracion) y ejecute el punto de entrada del plugin con el archivo como argumento:

```bash
pandora_kubernetes --conf <PATH_TO_CONFIG>
```

La interfaz de línea de comandos solo acepta `--conf`, por lo que todas las opciones se fijan a través del archivo de configuración. Cuando el plugin se ejecuta como tarea de Discovery, el servidor de Discovery construye ese archivo a partir de los campos de la tarea.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La ejecución informa de un error de petición | Confirme **Kubernetes host** y **Kubernetes port**, que el servidor de API sea accesible desde el servidor de Discovery y que el host no incluya un esquema. |
| Las peticiones fallan con `401` o `403` | El token falta, no es válido o no tiene acceso de lectura a los recursos consultados. Los endpoints de salud y los estados de componentes pueden necesitar permisos elevados. |
| No se generan deployments ni pods pero sí nodos | Revise **Filter namespace**: cuando está habilitado, los nombres deben coincidir de forma exacta y con las mismas mayúsculas, y una lista vacía no coincide con nada. |
| Faltan pods esperados | Solo se descubren los pods ya planificados en un nodo. Un pod en `Pending` sin nodo asignado no se genera. |
| Faltan los módulos de CPU y memoria de los nodos | La API de métricas de Kubernetes no está disponible en el clúster. |
| Faltan algunos módulos globales, de salud o de componentes | Esos endpoints devolvieron `401`, `403` o `404`, o la opción de escaneo correspondiente está deshabilitada. El plugin omite un endpoint opcional no accesible en lugar de hacer fallar toda la ejecución. |
| **API status** es `0` | El endpoint `/healthz` no devolvió `ok`. Compruebe la salud del propio servidor de API. |
| Las peticiones a la API agotan el tiempo | Las peticiones usan un tiempo de espera fijo de 5 segundos que no es configurable. Confirme la latencia entre el servidor de Discovery y el servidor de API. |
| Falla la transferencia por Tentacle | Confirme que el servidor de Discovery puede alcanzar **Tentacle IP** en **Tentacle port**. |
| El agente global usa modo proxy pero no se autentica | Cuando **Use proxy** está habilitado, el plugin envía las peticiones a **Proxy url** y no añade el token Bearer. |

## Referencia

### Parámetros de la tarea

La consola presenta estos campos después de la definición genérica de la tarea. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Kubernetes base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Kubernetes host | `_ip_` | string | — | Dirección o nombre del servidor de API, sin esquema |
| Kubernetes port | `_port_` | number | — | Puerto del servidor de API |
| Kubernetes token | `_token_` | textarea | — | Token Bearer usado para autenticarse contra la API. Necesario para leer los endpoints protegidos |
| Use prefix | `_usePrefix_` | checkbox | off | Antepone un prefijo a cada nombre de agente generado |
| Prefix | `_prefix_` | string | — | Prefijo usado cuando **Use prefix** está habilitado |
| Filter namespace | `_filterNamespace_` | checkbox | off | Restringe el descubrimiento a los namespaces indicados |
| Namespace | `_namespace_` | textarea | `[]` | Array JSON de namespaces, por ejemplo `["default","kube-system"]`. Se muestra cuando **Filter namespace** está habilitado |
| Use proxy | `_useProxy_` | checkbox | off | Enruta las peticiones a la API a través de **Proxy url** |
| Proxy url | `_proxyUrl_` | string | — | URL base del proxy. Se muestra cuando **Use proxy** está habilitado |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Destino de la transferencia por Tentacle |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de destino de la transferencia por Tentacle |

#### Kubernetes detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Scan Deployments | `_scanDeployments_` | checkbox | on | Genera un agente por deployment |
| Scan Nodes | `_scanNodes_` | checkbox | on | Genera un agente por nodo |
| Scan Pods | `_scanPods_` | checkbox | on | Genera un agente por pod planificado |
| Scan API health checks | `_healthChecks_` | checkbox | on | Genera los módulos de los endpoints de salud de la API. Puede necesitar permisos de API elevados |
| Scan component statuses | `_componentChecks_` | checkbox | on | Genera el recuento de componentes y los módulos de condiciones de componente. Puede necesitar permisos de API elevados |

### Claves del archivo de configuración

La tarea de Discovery construye este archivo a partir de sus propios campos; una ejecución manual lo suministra con `--conf`. Es un archivo de texto plano de líneas `key=value`.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `ip` | Dirección o nombre del servidor de API de Kubernetes | Vacío |
| `port` | Puerto del servidor de API de Kubernetes | Vacío |
| `token` | Token Bearer para la API | Vacío |
| `agents_group_name` | Grupo de agentes heredado de la tarea de Discovery | De la tarea |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` |
| `transfer_mode` | Método de transferencia de los datos generados | `tentacle` |
| `tentacle_ip` | Dirección de destino de Tentacle | `127.0.0.1` |
| `tentacle_port` | Puerto de destino de Tentacle | `41121` |
| `use_prefix` | `1` antepone el prefijo a cada nombre de agente | `0` |
| `prefix` | Prefijo de los nombres de agente generados | Vacío |
| `use_namespace` | `1` restringe deployments y pods a los namespaces indicados | `0` |
| `filter_namespace` | Array JSON de namespaces | `[]` |
| `use_proxy` | `1` enruta las peticiones a `proxy_url` y no añade el token Bearer | `0` |
| `proxy_url` | URL base del proxy | Vacío |
| `deployments` | `1` habilita el descubrimiento de deployments | `1` |
| `nodes` | `1` habilita el descubrimiento de nodos | `1` |
| `pods` | `1` habilita el descubrimiento de pods | `1` |
| `health_checks` | `1` habilita los módulos de los endpoints de salud de la API | `1` |
| `component_checks` | `1` habilita los módulos de estado de componentes | `1` |

### Línea de comandos

| Comando | Descripción |
| --- | --- |
| `pandora_kubernetes --conf <PATH_TO_CONFIG>` | Ejecuta el plugin con un archivo de configuración |

### Módulos generados

#### Agente global

| Nombre del módulo | Tipo | Qué informa |
| --- | --- | --- |
| `API status` | generic_proc | `1` cuando `/healthz` devuelve `ok`, `0` en caso contrario. Solo se crea cuando `/healthz` responde |
| Un módulo por endpoint de salud | generic_proc | `1` cuando el endpoint devuelve `ok`. Solo cuando **Scan API health checks** está habilitado |
| `Services` | generic_data | Número de servicios |
| `Namespaces` | generic_data | Número de namespaces |
| `Components` | generic_data | Número de estados de componentes. Solo cuando **Scan component statuses** está habilitado |
| `<componente>.<condición>` | generic_data | `1` cuando el estado de la condición del componente es `TRUE`, `0` en caso contrario |
| `Deployments` | generic_data | Número de deployments |

Los módulos de endpoints de salud consultan estas rutas: `/healthz`, `/healthz/ping`, `/healthz/log`, `/healthz/etcd` y los endpoints `/healthz/poststarthook/...` que expone el servidor de API. Solo se crea un módulo para un endpoint que responde.

#### Agentes de nodo

| Nombre del módulo | Tipo | Unidad | Qué informa |
| --- | --- | --- | --- |
| `Pods` | generic_data | — | Pods planificados actualmente en el nodo |
| `Pods (%)` | generic_data | % | Pods planificados frente a los pods asignables del nodo. Solo se crea cuando el nodo informa de pods asignables |
| `CPU (cores)` | generic_data | cores | CPU usada por el nodo. Requiere la API de métricas |
| `CPU (%)` | generic_data | % | CPU usada frente a la CPU asignable. Requiere la API de métricas |
| `Memory (bytes)` | generic_data | bytes | Memoria usada por el nodo. Requiere la API de métricas |
| `Memory (%)` | generic_data | % | Memoria usada frente a la memoria asignable. Requiere la API de métricas |
| `NetworkUnavailable`, `MemoryPressure`, `DiskPressure`, `PIDPressure`, `Ready` | generic_proc | — | Estado de la condición del nodo |

Los módulos de CPU y memoria del nodo solo se crean cuando el nodo expone los valores de la API de métricas y se conocen su CPU y memoria asignables.

#### Agentes de deployment

| Nombre del módulo | Tipo | Unidad | Qué informa |
| --- | --- | --- | --- |
| `Ready` | generic_proc | — | `1` cuando las réplicas listas igualan las réplicas deseadas, `0` en caso contrario |
| `Age` | generic_data | timeticks | Tiempo transcurrido desde la creación del deployment |
| `Replicas` | generic_data | — | Réplicas deseadas |
| `Updated replicas` | generic_data | — | Réplicas actualizadas a la plantilla deseada |
| `Ready replicas` | generic_data | — | Réplicas listas |
| `Available replicas` | generic_data | — | Réplicas disponibles |
| `Unavailable replicas` | generic_data | — | Réplicas que aún faltan para que el deployment alcance la disponibilidad total |
| `Available` | generic_data | — | Condición del deployment (`Available` o `Progressing`). Umbral de aviso en `2`, crítico en `0` |

#### Agentes de pod

| Nombre del módulo | Tipo | Unidad | Qué informa |
| --- | --- | --- | --- |
| `Pod status` | generic_data | — | Fase del pod: `0` Failed, `1` Running, `2` Succeeded, `3` Pending, `4` Unknown u otra |
| `PodScheduled`, `Ready`, `Initialized`, `Unschedulable`, `ContainersReady` | generic_proc | — | Estado de la condición del pod |
| `Containers` | generic_data | — | Número de contenedores del pod |
| `Container <nombre> CPU (cores)` | generic_data | cores | CPU usada por el contenedor. Requiere la API de métricas |
| `Container <nombre> CPU (%)` | generic_data | % | CPU usada por el contenedor frente a la CPU asignable de su nodo. Requiere la API de métricas |
| `Container <nombre> memory (bytes)` | generic_data | bytes | Memoria usada por el contenedor. Requiere la API de métricas |
| `Container <nombre> memory (%)` | generic_data | % | Memoria usada por el contenedor frente a la memoria asignable de su nodo. Requiere la API de métricas |

Solo se crea un módulo por contenedor cuando el contenedor expone esa métrica.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.kubernetes` |
| Versión del plugin | `1.3` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
