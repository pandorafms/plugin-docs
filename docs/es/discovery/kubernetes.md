# Kubernetes Discovery

*Última actualización del artículo: 2026-10-26.*

<!-- DRAFT: Verificado contra las fuentes del paquete 1.3; faltan validar la instalación del paquete distribuido y la recopilación en un entorno real. -->

## Qué monitoriza

El plugin de Discovery de Kubernetes se conecta al servidor de API del clúster y descubre sus cargas de trabajo e infraestructura: nodos, pods, deployments, namespaces, servicios, estados de componentes y endpoints de salud de la API. Genera un agente de Pandora FMS por recurso descubierto con módulos de disponibilidad, capacidad y rendimiento leídos de la API.

El plugin genera agentes para:

- el propio clúster, mediante un agente global **Kubernetes**;
- cada nodo, cuando **Scan Nodes** está habilitado;
- cada deployment con datos de condiciones, cuando **Scan Deployments** está habilitado;
- cada pod ya planificado en un nodo, cuando **Scan Pods** está habilitado.

El agente global también incluye el estado de la API, los endpoints de salud, el número de servicios, el número de namespaces y los estados de componentes del clúster.

El plugin se ejecuta como tarea de Discovery: la consola define la tarea, el servidor de Discovery ejecuta el plugin y los agentes y módulos se crean automáticamente. Los datos generados se envían mediante Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.3` (`pandorafms.kubernetes`) | Objetivo documentado | La versión que describe esta página, identificada por la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Clúster de Kubernetes con API accesible por HTTPS | `Requerido` | El plugin consulta `https://<host>:<port>`. Es un requisito, no una declaración de compatibilidad |
| Token Bearer con acceso de lectura a los recursos consultados | `Requerido` | Autenticación con `Authorization: Bearer <token>` para nodos, pods, deployments, servicios, namespaces y estados de componentes. Los endpoints de salud y de componentes pueden necesitar permisos elevados. Es un requisito, no una declaración de compatibilidad |
| API de métricas de Kubernetes (`metrics.k8s.io`) para el uso de CPU y memoria | `Requerido` para los módulos de CPU y memoria | Los módulos de CPU y memoria de nodos y contenedores se leen de `/apis/metrics.k8s.io/v1beta1`. Sin ella, los agentes de nodo y pod se siguen generando, pero esos módulos se omiten |
| Versión concreta de Kubernetes | `Sin validar` | No hay un registro de pruebas publicado que establezca compatibilidad con una versión concreta |
| Sistema operativo del host del plugin | `Sin validar` | No hay un registro de pruebas publicado que establezca compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea y una consola para definirla.
2. **Acceso al servidor de API desde el servidor de Discovery**, por host y puerto. La conexión directa usa HTTPS; introduzca el host sin esquema.
3. **Un token Bearer** para el servidor de API. Es necesario para leer los endpoints protegidos; concédale acceso de lectura solo a los recursos que consulta la tarea. Las opciones **Scan API health checks** y **Scan component statuses** pueden necesitar permisos de API elevados, como indican las ayudas de la tarea.
4. **Un grupo de agentes y un intervalo de monitorización**. Todos los agentes generados heredan ambos valores de la tarea.
5. **Conectividad al destino de Tentacle** para enviar los datos generados.
6. El plugin se distribuye como aplicación de Discovery de Pandora FMS (paquete `.disco`), ejecutada por el servidor de Discovery.

Las conexiones directas usan HTTPS sin verificar el certificado: la identidad del servidor no queda autenticada, por lo que funcionan los certificados autofirmados. Restrinja el acceso de red. En modo proxy se utiliza la URL indicada sin añadir la cabecera Bearer. El token se introduce en la tarea y se escribe en su configuración; restrinja el acceso a ambos. En ejecuciones manuales, guarde el token en un archivo protegido, no en comandos del shell.

### Comprobar el acceso al destino

Antes de crear la tarea, compruebe la API de métricas y las métricas de nodos y pods con una cuenta autorizada para el clúster:

```bash
kubectl get --raw /apis/metrics.k8s.io/v1beta1/
kubectl top node
kubectl top pod --all-namespaces
```

Si el clúster no expone la API de métricas, los agentes de nodo y pod se siguen generando, pero se omiten sus módulos de CPU y memoria. Estos comandos de diagnóstico no conceden permisos al token del plugin.

### Instalar el plugin

Obtenga el paquete `.disco` en la [entrada de Kubernetes del Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.kubernetes) y cárguelo en Discovery desde **Management → Discovery → Extension manager**. Una vez cargado, **Kubernetes** aparece en la categoría **Applications** del asistente de Discovery. Esta página corresponde al paquete `1.3`.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Kubernetes**. El asistente contiene la definición genérica y dos pasos del plugin: **Kubernetes base** y **Kubernetes detailed**. Todos los campos están en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Task definition

El paso genérico solicita el **nombre** de la tarea, el **grupo de agentes**, el **servidor** de ejecución y el **intervalo**. Todos los agentes generados heredan el grupo y el intervalo.

### Paso 2 — Kubernetes base

Conexión y destino de Tentacle:

- **Kubernetes host** es la dirección o el nombre del servidor de API.
- **Kubernetes port** es el puerto del servidor de API.
- **Kubernetes token** es el token Bearer de autenticación.
- **Use prefix** muestra **Prefix**, el texto que se antepone a las identidades de agentes. Vacíe **Prefix** al desactivar la opción: esta versión sigue aplicando un prefijo que conserve contenido.
- **Filter namespace** restringe el descubrimiento a los namespaces indicados en **Namespace**.
- **Use proxy** dirige las peticiones a **Proxy url**.
- **Tentacle IP** y **Tentacle port** indican el destino de los datos. Mantenga los valores predeterminados salvo que necesite otro destino.

![Paso Kubernetes base](../assets/images/discovery/kubernetes/kubernetes-base.png)

### Paso 3 — Kubernetes detailed

Selección de recursos:

- **Scan Deployments**, **Scan Nodes** y **Scan Pods** activan o desactivan cada categoría de recurso.
- **Scan API health checks** genera los módulos de los endpoints de salud de la API. Los endpoints de salud pueden necesitar permisos de API elevados.
- **Scan component statuses** genera el recuento de componentes y los módulos de condiciones de componente. Los estados de componentes pueden necesitar permisos de API elevados.

![Paso Kubernetes detailed](../assets/images/discovery/kubernetes/kubernetes-detailed.png)

## Verificar la primera ejecución

Ejecute la tarea desde **Management → Discovery → Task list** y compruebe:

1. **El resumen de la tarea**: progreso, agentes de nodo, pod y deployment generados y total de agentes.
2. **Los agentes**: el global **Kubernetes** y una instancia por cada nodo, deployment y pod planificado descubiertos. Los agentes de nodo y pod se generan aunque la API de métricas no esté disponible; los deployments requieren datos de condiciones.
3. **Los módulos**: cada agente generado lleva los módulos de su recurso; un clúster accesible con la API de métricas disponible rellena los valores de CPU y memoria. Los contadores del resumen no demuestran que los datos se hayan recibido correctamente.
4. **La información de ejecución**: una ejecución correcta no informa de errores; los fallos de peticiones se registran ahí.

![Resumen de ejecución de la tarea](../assets/images/discovery/kubernetes/task-summary.png)

Si la tarea falla antes de generar nada, revise primero host, puerto, conectividad y token.

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por recurso descubierto. Los nombres se forman con el nombre original del recurso y el prefijo opcional.

| Agente | Nombre | Agente padre |
| --- | --- | --- |
| Global | `[Prefix]Kubernetes` | — |
| Nodo | `[Prefix]<node>` | El agente global |
| Deployment | `[Prefix]<deployment>` | `Kubernetes` (sin prefijo) |
| Pod | `[Prefix]<namespace>/<pod>` | El agente del nodo que lo ejecuta |

Los nodos apuntan al global con prefijo; los deployments apuntan al padre `Kubernetes` sin prefijo aunque haya uno configurado. Los pods apuntan al nodo con prefijo y usan la IP del pod como dirección. Las descripciones son `Kubernetes global agent`, `Kubernetes node`, `Kubernetes deployment` y `Kubernetes pod`.

Los agentes de nodo y pod no dependen de la API de métricas: si no está disponible, se siguen generando sin los módulos de CPU y memoria. Solo se descubren los pods ya planificados en un nodo: un pod sin nodo asignado se omite, igual que los recursos que la API devuelve sin nombre. Las identidades de los pods incluyen el namespace, por lo que nombres iguales en namespaces distintos no colisionan; las de los deployments no incluyen el namespace, por lo que nombres iguales de deployment en namespaces distintos pueden colisionar. Use prefijos distintos para clústeres diferentes; filtrar namespaces no añade el namespace a la identidad del deployment.

Cambiar **Prefix** cambia la identidad de todos los agentes generados. **Filter namespace** solo afecta a deployments y pods; los nodos tienen ámbito de clúster. La comparación es exacta y distingue mayúsculas. La lista es un array JSON, por ejemplo `["default","kube-system"]`. Con el filtro activado, incluya al menos un namespace: una lista vacía no genera agentes de deployment ni de pod.

### Módulos por agente

Los valores se leen en cada ejecución. Los nombres, tipos y unidades están en [Módulos generados](#modulos-generados).

| Agente | Módulos |
| --- | --- |
| Global | Estado de la API, endpoints de salud, número de servicios, namespaces, estados de componentes y deployments |
| Nodo | Pods frente a capacidad asignable, condiciones y, cuando la API de métricas está disponible, uso de CPU y memoria |
| Deployment | Recuentos de réplicas, preparación y disponibilidad |
| Pod | Fase, condiciones, número de contenedores y, cuando la API de métricas está disponible, CPU y memoria por contenedor |

![Módulos de un agente de pod generado](../assets/images/discovery/kubernetes/pod-modules.png)

## Operar

### Ejecución manual

Para probar la conectividad o realizar una ejecución puntual fuera del asistente, escriba los pares `key=value` de [Claves del archivo de configuración](#claves-del-archivo-de-configuracion) y ejecute:

```bash
pandora_kubernetes --conf <PATH_TO_CONFIG>
```

Este ejemplo de configuración directa habilita todas las categorías de recursos y opciones de escaneo. Sustituya todos los marcadores antes de usarlo; el ejemplo no se ha ejecutado:

```ini
ip=<TARGET_HOST>
port=<API_PORT>
token=<API_TOKEN>
agents_group_name=<AGENT_GROUP>
interval=300
transfer_mode=tentacle
tentacle_ip=<TENTACLE_HOST>
tentacle_port=41121
prefix=<CLUSTER_PREFIX>
use_prefix=1
use_namespace=1
filter_namespace=["default","kube-system"]
use_proxy=0
deployments=1
nodes=1
pods=1
health_checks=1
component_checks=1
```

La ejecución devuelve un resumen JSON de Discovery y genera XML por agente. Un resumen ilustrativo es `{"summary":{"Total agents":4,"Nodes agents":1,"Pods agents":1,"Deployments agents":1}}`; los contadores describen la generación, no la entrega confirmada.

La entrada operativa de la CLI es `--conf` (`-h`/`--help` muestra ayuda). En una tarea de Discovery, el servidor construye el archivo a partir de los campos. Los ejemplos manuales no se han ejecutado contra un entorno real.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| Error de petición | Confirme **Kubernetes host**, **Kubernetes port** y conectividad desde Discovery. El host no debe incluir esquema. |
| Respuestas `401` o `403` | El token falta, no es válido o no permite leer el recurso. Los endpoints de salud y de componentes pueden necesitar permisos elevados. Compruebe el acceso a las rutas exactas de la referencia de API; esta página no proporciona un rol validado. |
| Se generan nodos, pero no deployments ni pods | Revise **Scan Deployments** y **Scan Pods**, y **Filter namespace**: con el filtro activado, los nombres deben coincidir de forma exacta y con las mismas mayúsculas; una lista vacía no coincide con nada. |
| Faltan pods esperados | Solo se descubren los pods ya planificados en un nodo. Un pod en `Pending` sin nodo asignado no se genera. |
| Faltan los módulos de CPU y memoria de los nodos | La API de métricas de Kubernetes no está disponible en el clúster. El agente de nodo se sigue generando. |
| Faltan algunos módulos globales, de salud o de componentes | Esos endpoints devolvieron `401`, `403` o `404`, o la opción de escaneo correspondiente está deshabilitada. El plugin omite un endpoint opcional no accesible en lugar de hacer fallar toda la ejecución. |
| **API status** es `0` | El endpoint `/healthz` no devolvió `ok`. Compruebe la salud del propio servidor de API. Si `/healthz` no es accesible, el módulo se omite. |
| Falta un agente de deployment | Revise **Scan Deployments**, el filtro de namespaces y las condiciones devueltas. |
| **Available** parece correcto con una condición fallida | Refleja el tipo de la primera condición, no su estado booleano. Contraste réplicas y condiciones con el clúster. |
| Las peticiones agotan el tiempo | El tiempo de espera es fijo de 5 segundos, no configurable. Revise la latencia. |
| Falla Tentacle | Compruebe el acceso desde Discovery a **Tentacle IP** y **Tentacle port**. |
| El modo proxy no se autentica | **Use proxy** envía las peticiones a **Proxy url** sin añadir el token Bearer. |

## Referencia

### Parámetros de la tarea

Estos campos siguen a la definición genérica. La macro identifica el valor en la configuración generada.

#### Kubernetes base

| Campo | Macro | Tipo | Requerido | Por defecto | Notas |
| --- | --- | --- | --- | --- | --- |
| Kubernetes host | `_ip_` | string | Modo directo | Vacío | Dirección o nombre del servidor de API, sin esquema |
| Kubernetes port | `_port_` | number | Modo directo | Vacío | Puerto numérico del servidor de API |
| Kubernetes token | `_token_` | textarea | Endpoints directos protegidos | Vacío | Token Bearer; el asistente permite dejarlo vacío |
| Use prefix | `_usePrefix_` | checkbox | No | off | Muestra el campo de prefijo; no anula un prefijo con contenido |
| Prefix | `_prefix_` | string | No | Vacío | Visible con **Use prefix**; vacíelo para dejar de aplicar prefijo |
| Filter namespace | `_filterNamespace_` | checkbox | No | off | Limita los agentes de deployment y de pod a la lista indicada |
| Namespace | `_namespace_` | textarea | Al filtrar | `[]` | Array JSON, por ejemplo `["default","kube-system"]`; comparación exacta con distinción de mayúsculas |
| Use proxy | `_useProxy_` | checkbox | No | off | Usa **Proxy url** en lugar de la dirección directa; omite autenticación Bearer |
| Proxy url | `_proxyUrl_` | string | Modo proxy | Vacío | URL base con esquema; visible con **Use proxy** |
| Tentacle IP | `_tentacleIP_` | string | Sí | `127.0.0.1` | Destino de transferencia |
| Tentacle port | `_tentaclePort_` | number | Sí | `41121` | Puerto numérico de transferencia |

#### Kubernetes detailed

| Campo | Macro | Tipo | Requerido | Por defecto | Notas |
| --- | --- | --- | --- | --- | --- |
| Scan Deployments | `_scanDeployments_` | checkbox | No | on | Genera agentes de deployment cuando hay datos de condiciones |
| Scan Nodes | `_scanNodes_` | checkbox | No | on | Genera agentes de nodo; los módulos de CPU y memoria requieren la API de métricas |
| Scan Pods | `_scanPods_` | checkbox | No | on | Genera agentes de pod planificados; los módulos de CPU y memoria por contenedor requieren la API de métricas |
| Scan API health checks | `_healthChecks_` | checkbox | No | on | Genera los módulos de los endpoints de salud de la API. Puede necesitar permisos de API elevados |
| Scan component statuses | `_componentChecks_` | checkbox | No | on | Genera el recuento de componentes y los módulos de condiciones de componente. Puede necesitar permisos de API elevados |

### Claves del archivo de configuración

La tarea construye este archivo a partir de sus campos; en modo manual se indica con `--conf`. Es texto plano con líneas `key=value`.

En modo directo se requieren `ip`, `port` y, para endpoints protegidos, `token`; en modo proxy, `proxy_url`; para enviar datos, `transfer_mode=tentacle` y `tentacle_ip`. Las demás claves son opcionales con los valores siguientes. Proteja el archivo porque contiene el token.

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ip` | Modo directo | Vacío | Host de la API sin esquema |
| `port` | Modo directo | Vacío | Puerto de la API |
| `token` | Endpoints directos protegidos | Vacío | Token Bearer |
| `agents_group_name` | No | Vacío en manual; grupo de la tarea | Grupo de destino |
| `interval` | No | `300` | Intervalo de agentes en segundos; el de la tarea en Discovery |
| `transfer_mode` | Para enviar | Vacío en manual; `tentacle` en tarea | Use `tentacle` para la transferencia documentada |
| `tentacle_ip` | Para Tentacle | Vacío en manual; `127.0.0.1` en tarea | Destino de transferencia |
| `tentacle_port` | No | `41121` | Puerto de transferencia |
| `use_prefix` | No | `0` | Muestra el campo de la tarea; no anula un `prefix` con contenido |
| `prefix` | No | Vacío | Prefijo de identidades de agentes |
| `use_namespace` | No | `0` | `1` habilita el filtro de namespaces de cargas de trabajo |
| `filter_namespace` | Al filtrar | `[]` | Array JSON; coincidencia exacta de namespaces |
| `use_proxy` | No | `0` | `1` usa `proxy_url` sin cabecera Bearer |
| `proxy_url` | Modo proxy | Vacío | URL base con esquema |
| `deployments` | No | `1` | `1` recopila deployments y genera agentes de deployment |
| `nodes` | No | `1` | `1` recopila nodos y genera agentes de nodo |
| `pods` | No | `1` | `1` recopila pods y genera agentes de pod |
| `health_checks` | No | `1` | `1` genera los módulos de los endpoints de salud de la API |
| `component_checks` | No | `1` | `1` genera los módulos de estado de componentes |
| `data_dir` | No | Vacío | Aceptada, pero no selecciona el directorio de salida |

### Línea de comandos

| Comando | Descripción |
| --- | --- |
| `pandora_kubernetes --conf <PATH_TO_CONFIG>` | Ejecuta el plugin con un archivo de configuración |

### Módulos generados

#### Agente global

| Nombre | Tipo | Valor |
| --- | --- | --- |
| `API status` | generic_proc | `1` si `/healthz` devuelve `ok`; `0` en caso contrario. Solo se crea cuando `/healthz` responde |
| Un módulo por endpoint de salud | generic_proc | `1` si devuelve `ok`; `0` en caso contrario. Solo cuando **Scan API health checks** está habilitado y el endpoint responde |
| `Services` | generic_data | Número de servicios; se omite si la petición no es accesible |
| `Namespaces` | generic_data | Número de namespaces; se omite si la petición no es accesible |
| `Components` | generic_data | Número de estados de componentes. Solo cuando **Scan component statuses** está habilitado y la petición es accesible |
| `<component>.<condition>` | generic_data | `1` si el estado es `TRUE`; `0` en caso contrario |
| `Deployments` | generic_data | Número de deployments; `0` cuando **Scan Deployments** está deshabilitado |

Los nombres y rutas de salud están en [Peticiones a la API](#peticiones-a-la-api). Solo se crea un módulo para un endpoint que responde. Los fallos de endpoints opcionales no impiden la transferencia del agente global.

#### Agentes de nodo

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Pods` | generic_data | — | Pods contados durante la recopilación en el nodo |
| `Pods (%)` | generic_data | % | Pods recopilados frente a capacidad asignable del nodo; se omite si falta esa capacidad |
| `CPU (cores)` | generic_data | cores | CPU utilizada; requiere API de métricas |
| `CPU (%)` | generic_data | % | CPU utilizada frente a asignable; requiere API de métricas |
| `Memory (bytes)` | generic_data | bytes | Memoria utilizada; requiere API de métricas |
| `Memory (%)` | generic_data | % | Memoria utilizada frente a asignable; requiere API de métricas |
| `NetworkUnavailable`, `MemoryPressure`, `DiskPressure`, `PIDPressure` | generic_proc | — | `1` si la condición es `False`; `0` en caso contrario |
| `Ready` | generic_proc | — | `1` si la condición es `True`; `0` en caso contrario |

Los agentes de nodo se generan aunque la API de métricas no esté disponible; en ese caso se omiten los módulos de CPU y memoria. `Pods` cuenta los pods procesados de los datos recibidos, no un recuento independiente validado de todos los pods del nodo.

#### Agentes de deployment

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Ready` | generic_proc | — | `1` si las réplicas listas igualan las deseadas; `0` en caso contrario |
| `Age` | generic_data | `_timeticks_` | Fecha de creación en centésimas de segundo desde 1970, no edad transcurrida |
| `Replicas` | generic_data | — | Réplicas deseadas |
| `Updated replicas` | generic_data | — | Réplicas actualizadas a la plantilla deseada |
| `Ready replicas` | generic_data | — | Réplicas listas |
| `Available replicas` | generic_data | — | Réplicas disponibles |
| `Unavailable replicas` | generic_data | — | Réplicas restantes para alcanzar disponibilidad completa |
| `Available` | generic_data | — | `1` si el tipo de la primera condición es `Available` o `Progressing`; `0` en otro caso. Ignora el estado de la condición. Umbral de aviso `2` y crítico `0` |

Los agentes de deployment solo se generan cuando el deployment devuelve al menos una condición.

#### Agentes de pod

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Pod status` | generic_data | — | `0` Failed, `1` Running, `2` Succeeded, `3` Pending, `4` Unknown u otro |
| `PodScheduled`, `Ready`, `Initialized`, `ContainersReady` | generic_proc | — | `1` para condición `True`; `0` en otro caso |
| `Unschedulable` | generic_proc | — | `1` para condición `False`; `0` en otro caso |
| `Containers` | generic_data | — | Número de contenedores |
| `Container <name> CPU (cores)` | generic_data | cores | CPU del contenedor; requiere API de métricas |
| `Container <name> CPU (%)` | generic_data | % | CPU frente a la asignable del nodo; requiere API de métricas |
| `Container <name> memory (bytes)` | generic_data | bytes | Memoria del contenedor; requiere API de métricas |
| `Container <name> memory (%)` | generic_data | % | Memoria frente a la asignable del nodo; requiere API de métricas |

Solo se crea un módulo de CPU o memoria por contenedor cuando el contenedor expone esa métrica; el agente de pod se genera aunque falte una métrica. Los porcentajes usan los recursos asignables del nodo, no los requests ni límites del contenedor.

### Peticiones a la API

El token necesita acceso a las siguientes peticiones. Los interruptores de recursos controlan la recopilación y la generación de agentes; los de salud y componentes controlan sus propias peticiones. Esta lista describe las consultas, no un rol de mínimo privilegio validado.

| Recurso | Ruta GET |
| --- | --- |
| Nodos y detalles de nodo | `/api/v1/nodes`, `/api/v1/nodes/<NODE_NAME>` |
| Pods | `/api/v1/pods` |
| Métricas | `/apis/metrics.k8s.io/v1beta1/nodes`, `/apis/metrics.k8s.io/v1beta1/pods` |
| Deployments | `/apis/apps/v1/deployments` |
| Servicios | `/api/v1/services` |
| Namespaces | `/api/v1/namespaces` |
| Estados de componentes | `/api/v1/componentstatuses` |

| Módulo de salud | Ruta GET |
| --- | --- |
| `healthz` | `/healthz` |
| `healthzPing` | `/healthz/ping` |
| `healthzLog` | `/healthz/log` |
| `healthzEtcd` | `/healthz/etcd` |
| `healthzPoststarthook crd informer synced` | `/healthz/poststarthook/crd-informer-synced` |
| `healthzPoststarthook generic apiserver start informers` | `/healthz/poststarthook/generic-apiserver-start-informers` |
| `healthzPoststarthook start apiextensions controllers` | `/healthz/poststarthook/start-apiextensions-controllers` |
| `healthzPoststarthook start apiextensions informers` | `/healthz/poststarthook/start-apiextensions-informers` |

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.kubernetes` |
| Versión del plugin | `1.3` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
