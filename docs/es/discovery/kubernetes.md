# Kubernetes Discovery

*Última actualización del artículo: 2026-10-23.*

<!-- DRAFT: Verificado contra las fuentes del paquete 1.2; faltan validar la instalación del paquete distribuido y la recopilación en un entorno real. -->

## Qué monitoriza

El plugin de Discovery de Kubernetes se conecta al servidor de API del clúster y descubre sus cargas de trabajo e infraestructura: nodos, pods, deployments, namespaces, servicios, estados de componentes y endpoints de salud de la API. Genera un agente de Pandora FMS por recurso descubierto con módulos de disponibilidad, capacidad y rendimiento leídos de la API.

El plugin genera agentes para:

- el propio clúster, mediante un agente global **Kubernetes**;
- cada nodo, cuando **Scan Nodes** está habilitado;
- cada deployment, cuando **Scan Deployments** está habilitado;
- los pods con métricas y datos completos de nodo e IP, cuando **Scan Pods** está habilitado.

El agente global también incluye el estado de la API, los endpoints de salud, el número de servicios, el número de namespaces y los estados de componentes del clúster.

El plugin se ejecuta como tarea de Discovery: la consola define la tarea, el servidor de Discovery ejecuta el plugin y los agentes y módulos se crean automáticamente. Los datos generados se envían mediante Tentacle.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.2` (`pandorafms.kubernetes`) | Objetivo documentado | Identidad del paquete; consulte [Identidad del plugin](#identidad-del-plugin) |
| Clúster de Kubernetes con API accesible por HTTPS | `Requerido` | El plugin consulta `https://<host>:<port>`. Es un requisito, no una declaración de compatibilidad |
| Token Bearer con acceso de lectura a los recursos consultados | `Requerido` | Autenticación con `Authorization: Bearer <token>` para nodos, pods, deployments, servicios, namespaces y estados de componentes |
| API de métricas de Kubernetes (`metrics.k8s.io`) | `Requerido` para descubrir nodos y pods | Los datos parten de `/apis/metrics.k8s.io/v1beta1`; su ausencia puede impedir generar agentes, no solo omitir CPU y memoria |
| Versión concreta de Kubernetes | `Sin validar` | No hay un registro de pruebas publicado que establezca compatibilidad con una versión concreta |
| Sistema operativo del host del plugin | `Sin validar` | No hay un registro de pruebas publicado que establezca compatibilidad con sistemas operativos |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea y una consola para definirla.
2. **Acceso al servidor de API desde el servidor de Discovery**, por host y puerto. La conexión directa usa HTTPS; introduzca el host sin esquema.
3. **Un token Bearer** con acceso de lectura a nodos, pods, deployments, namespaces, servicios, estados de componentes, métricas de nodos y pods y los endpoints de salud de [Peticiones a la API](#peticiones-a-la-api). La tarea no define un rol concreto. Las peticiones de salud y componentes siempre se intentan; esta versión no tiene interruptores para ellas.
4. **Un grupo de agentes y un intervalo de monitorización**. Todos los agentes generados heredan ambos valores de la tarea.
5. **Conectividad al destino de Tentacle** para enviar los datos generados.
6. El plugin se distribuye como aplicación de Discovery de Pandora FMS (paquete `.disco`), ejecutada por el servidor de Discovery.

Las conexiones directas usan HTTPS sin verificar el certificado: la identidad del servidor no queda autenticada. Restrinja el acceso de red. En modo proxy se utiliza la URL indicada sin añadir la cabecera Bearer. El token se introduce en la tarea y se escribe en su configuración; restrinja el acceso a ambos. En ejecuciones manuales, guarde el token en un archivo protegido, no en comandos del shell.

### Comprobar el acceso al destino

Antes de crear la tarea, compruebe la API de métricas y las métricas de nodos y pods con una cuenta autorizada para el clúster:

```bash
kubectl get --raw /apis/metrics.k8s.io/v1beta1/
kubectl top node
kubectl top pod --all-namespaces
```

Si el clúster no expone la API de métricas, su administrador debe configurarla antes de verificar el descubrimiento de nodos y pods. Estos comandos de diagnóstico no conceden permisos al token del plugin.

### Instalar el plugin

Obtenga el paquete `.disco` en la [entrada de Kubernetes del Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.kubernetes) y cárguelo en Discovery. Seleccione **Kubernetes** al crear una tarea de aplicación. Esta página corresponde al paquete `1.2`, no a una interfaz `1.3`.

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

- **Scan Deployments**, **Scan Nodes** y **Scan Pods** activan o desactivan la generación de agentes por categoría. Las peticiones de recopilación se ejecutan aunque estas opciones estén desactivadas.
- El paquete `1.2` no tiene interruptores para los endpoints de salud ni los estados de componentes.

<!-- SCREENSHOT NEEDED: Paso Kubernetes detailed de la versión 1.2 con solo los tres interruptores de recursos; la imagen heredada de 1.3 no corresponde. -->

## Verificar la primera ejecución

Ejecute la tarea desde **Management → Discovery → Task list** y compruebe:

1. **El resumen de la tarea**: progreso, agentes de nodo, pod y deployment generados y total de agentes.
2. **Los agentes**: el global **Kubernetes** y las categorías habilitadas. Los nodos y pods dependen de las métricas; los deployments requieren datos de condiciones.
3. **Los módulos**: contraste valores representativos de CPU y memoria y condiciones de pods con el clúster. Los contadores del resumen no demuestran que los datos se hayan recibido correctamente.
4. **La información de ejecución**: una ejecución correcta no informa de errores; los fallos de peticiones se registran ahí.

Si no se genera nada, revise primero host, puerto, conectividad y token.

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por recurso descubierto. Los nombres se forman con el nombre original del recurso y el prefijo opcional.

| Agente | Nombre | Agente padre |
| --- | --- | --- |
| Global | `[Prefix]Kubernetes` | — |
| Nodo | `[Prefix]<node>` | El agente global |
| Deployment | `[Prefix]<deployment>` | `Kubernetes` (sin prefijo) |
| Pod | `[Prefix]<pod>` | El agente del nodo que lo ejecuta |

Los nodos apuntan al global con prefijo; los deployments apuntan al padre `Kubernetes` sin prefijo aunque haya uno configurado. Los pods apuntan al nodo con prefijo y usan la IP del pod como dirección. Las descripciones son `Kubernetes global agent`, `Kubernetes node`, `Kubernetes deployment` y `Kubernetes pod`.

El descubrimiento de nodos y pods parte de la API de métricas. Las métricas incompletas, la ausencia de nodo asignado o de IP del pod pueden interrumpir el procesamiento y dejar resultados parciales. Las identidades de pods y deployments no incluyen el namespace: nombres iguales en namespaces distintos pueden colisionar. Use prefijos distintos para clústeres diferentes; filtrar namespaces no añade el namespace a la identidad.

Cambiar **Prefix** cambia la identidad de todos los agentes generados. **Filter namespace** solo afecta a deployments y pods; los nodos tienen ámbito de clúster. La comparación es exacta y distingue mayúsculas. La lista es un array JSON, por ejemplo `["default","kube-system"]`. Con el filtro activado, incluya al menos un namespace: una lista vacía no genera agentes de deployment ni de pod.

### Módulos por agente

Los valores se leen en cada ejecución. Los nombres, tipos y unidades están en [Módulos generados](#modulos-generados).

| Agente | Módulos |
| --- | --- |
| Global | Estado de la API, endpoints de salud, número de servicios, namespaces, estados de componentes y deployments |
| Nodo | Pods frente a capacidad asignable, condiciones, CPU y memoria; depende de la API de métricas |
| Deployment | Recuentos de réplicas, preparación y disponibilidad |
| Pod | Fase, condiciones, número de contenedores y CPU/memoria por contenedor; depende de la API de métricas |

![Módulos de un agente de pod generado](../assets/images/discovery/kubernetes/pod-modules.png)

## Operar

### Ejecución manual

Para probar la conectividad o realizar una ejecución puntual fuera del asistente, escriba los pares `key=value` de [Claves del archivo de configuración](#claves-del-archivo-de-configuracion) y ejecute:

```bash
pandora_kubernetes --conf <PATH_TO_CONFIG>
```

Este ejemplo de configuración directa habilita las tres categorías de recursos. Sustituya todos los marcadores antes de usarlo; el ejemplo no se ha ejecutado:

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
```

La ejecución devuelve un resumen JSON de Discovery y genera XML por agente. Un resumen ilustrativo es `{"summary":{"Total agents":4,"Nodes agents":1,"Pods agents":1,"Deployments agents":1}}`; los contadores describen la generación, no la entrega confirmada.

La entrada operativa de la CLI es `--conf` (`-h`/`--help` muestra ayuda). En una tarea de Discovery, el servidor construye el archivo a partir de los campos. Los ejemplos manuales no se han ejecutado contra un entorno real.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| Error de petición | Confirme **Kubernetes host**, **Kubernetes port** y conectividad desde Discovery. El host no debe incluir esquema. |
| Respuestas `401` o `403` | El token falta, no es válido o no permite leer el recurso. Compruebe el acceso a las rutas exactas de la referencia de API; esta página no proporciona un rol validado. |
| Se generan nodos, pero no deployments ni pods | Revise **Filter namespace**: coincidencia exacta con las mismas mayúsculas; una lista vacía no coincide con nada. |
| Faltan pods esperados | Compruebe métricas, nodo asignado e IP. Los datos incompletos pueden interrumpir la generación; no presuponga que todos los pods pendientes se omiten sin errores. |
| Faltan agentes o módulos de nodo/pod | Revise la API de métricas, los recursos asignables y los datos de nodo/IP del pod. Consulte `Can't get metrics`, `Error: Nodes` y `Error: Pods`: los datos incompletos pueden detener el procesamiento. |
| Faltan módulos globales, de salud o componentes | Revise errores de peticiones, incluidos `401`, `403` y `404`. Los fallos de endpoints de salud omiten sus módulos; los fallos al consultar servicios, namespaces o componentes pueden impedir enviar el global. No hay interruptor para omitir estas peticiones. |
| `Could not connect to the API` o **API status** a `0` | `/healthz` no devuelve exactamente `ok`. Revise acceso y salud de la API; también es la comprobación inicial de conexión. |
| Falta un agente de deployment | Revise **Scan Deployments**, filtro de namespaces y condiciones devueltas. |
| **Available** parece correcto con una condición fallida | Refleja el tipo de la primera condición, no su estado booleano. Contraste réplicas y condiciones con el clúster. |
| Las peticiones agotan el tiempo | El tiempo de espera es fijo de 5 segundos, no configurable. Revise la latencia. |
| Falla Tentacle | Compruebe acceso desde Discovery a **Tentacle IP** y **Tentacle port**. |
| El modo proxy no se autentica | **Use proxy** envía las peticiones a **Proxy url** sin añadir el token Bearer. |

## Referencia

### Parámetros de la tarea

Estos campos siguen a la definición genérica. La macro identifica el valor en la configuración generada.

#### Kubernetes base

| Campo | Macro | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- | --- |
| Kubernetes host | `_ip_` | Modo directo | Vacío | Dirección o nombre del servidor de API, sin esquema |
| Kubernetes port | `_port_` | Modo directo | Vacío | Puerto numérico del servidor de API |
| Kubernetes token | `_token_` | Endpoints directos protegidos | Vacío | Token Bearer; el asistente permite dejarlo vacío |
| Use prefix | `_usePrefix_` | No | off | Muestra el campo de prefijo |
| Prefix | `_prefix_` | No | Vacío | Visible con **Use prefix**; vacíelo para dejar de aplicar prefijo |
| Filter namespace | `_filterNamespace_` | No | off | Limita agentes de deployment y pod a la lista indicada |
| Namespace | `_namespace_` | Al filtrar | `[]` | Array JSON, por ejemplo `["default","kube-system"]`; comparación exacta con distinción de mayúsculas |
| Use proxy | `_useProxy_` | No | off | Usa **Proxy url** en lugar de la dirección directa; omite autenticación Bearer |
| Proxy url | `_proxyUrl_` | Modo proxy | Vacío | URL base con esquema; visible con **Use proxy** |
| Tentacle IP | `_tentacleIP_` | Sí | `127.0.0.1` | Destino de transferencia |
| Tentacle port | `_tentaclePort_` | Sí | `41121` | Puerto numérico de transferencia |

#### Kubernetes detailed

| Campo | Macro | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- | --- |
| Scan Deployments | `_scanDeployments_` | No | on | Genera agentes de deployment cuando hay condiciones |
| Scan Nodes | `_scanNodes_` | No | on | Genera agentes de nodo a partir de métricas disponibles |
| Scan Pods | `_scanPods_` | No | on | Genera agentes de pod con datos completos de métricas, nodo e IP |

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
| `deployments` | No | `1` | `1` genera agentes de deployment |
| `nodes` | No | `1` | `1` genera agentes de nodo |
| `pods` | No | `1` | `1` genera agentes de pod |
| `data_dir` | No | Vacío | Aceptada, pero no selecciona el directorio de salida |

### Línea de comandos

| Comando | Descripción |
| --- | --- |
| `pandora_kubernetes --conf <PATH_TO_CONFIG>` | Ejecuta el plugin con un archivo de configuración |

### Módulos generados

#### Agente global

| Nombre | Tipo | Valor |
| --- | --- | --- |
| `API status` | generic_proc | `1` si `/healthz` devuelve `ok`; `0` en caso contrario |
| Un módulo por endpoint de salud | generic_proc | `1` si devuelve `ok`; `0` en caso contrario; se omite si falla la petición |
| `Services` | generic_data | Número de servicios |
| `Namespaces` | generic_data | Número de namespaces |
| `Components` | generic_data | Número de estados de componentes |
| `<component>.<condition>` | generic_data | `1` si el estado es `TRUE`; `0` en caso contrario |
| `Deployments` | generic_data | Número de deployments |

Los nombres y rutas de salud están en [Peticiones a la API](#peticiones-a-la-api). El global se transfiere solo si termina su fase de recopilación.

#### Agentes de nodo

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Pods` | generic_data | — | Pods contados durante la recopilación en el nodo |
| `Pods (%)` | generic_data | % | Pods recopilados frente a capacidad asignable del nodo; su ausencia puede detener la generación de nodos |
| `CPU (cores)` | generic_data | cores | CPU utilizada; requiere API de métricas |
| `CPU (%)` | generic_data | % | CPU utilizada frente a asignable; requiere API de métricas |
| `Memory (bytes)` | generic_data | bytes | Memoria utilizada; requiere API de métricas |
| `Memory (%)` | generic_data | % | Memoria utilizada frente a asignable; requiere API de métricas |
| `NetworkUnavailable`, `MemoryPressure`, `DiskPressure`, `PIDPressure` | generic_proc | — | `1` si la condición es `False`; `0` en caso contrario |
| `Ready` | generic_proc | — | `1` si la condición es `True`; `0` en caso contrario |

La generación de nodos requiere métricas y datos asignables completos, incluida la capacidad de pods. La ausencia de campos puede detener la fase de nodos en lugar de generar agentes con menos módulos. `Pods` cuenta los pods procesados de los datos recibidos, no un recuento independiente validado de todos los pods del nodo.

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

Las métricas incompletas de contenedores pueden interrumpir la generación del agente. Los porcentajes usan los recursos asignables del nodo, no los requests ni límites del contenedor.

### Peticiones a la API

El token necesita acceso a las siguientes peticiones. Los interruptores controlan la generación de agentes, no la recopilación. Esta lista describe las consultas, no un rol de mínimo privilegio validado.

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
| Versión del plugin | `1.2` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
