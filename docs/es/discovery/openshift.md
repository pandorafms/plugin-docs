# OpenShift Discovery

*Última actualización del artículo: 2026-10-23.*

<!-- DRAFT: Verificación estática del paquete Discovery 1.0; faltan validar instalación, interfaz de esta versión y recopilación en un entorno real. -->

## Qué monitoriza

OpenShift Discovery consulta la API del clúster y genera un agente global y agentes de nodos, pods y deployments. La tarea genera XML de agentes y lo envía mediante Tentacle. El global resume servicios, namespaces, estados de componentes, replication controllers y servicios de API; los agentes de recursos informan de capacidad, condiciones y CPU/memoria de contenedores.

Esta página corresponde a la aplicación de Discovery, no al antiguo plugin CLI/servidor de OpenShift. No reutilice sus opciones `cli`, `user`, `password`, `project`, `agent_*` ni `as_server_plugin` aquí.

## Preparación

### Compatibilidad y requisitos

| Ámbito | Estado | Requisito o limitación |
| --- | --- | --- |
| `pandorafms.openshift`, paquete `1.0` | Objetivo documentado | Aplicación de Discovery (`.disco`) |
| Servidor y consola de Pandora FMS con Discovery | Requerido | Definir y ejecutar la tarea de aplicación |
| API de OpenShift accesible desde Discovery | Requerido | Conexión directa a `https://<TARGET_HOST>:<API_PORT>` |
| Token Bearer | Requerido para endpoints directos protegidos | Lectura de recursos y rutas de salud de [Peticiones a la API](#peticiones-a-la-api); no se proporciona un rol de mínimo privilegio validado |
| API de métricas (`metrics.k8s.io/v1beta1`) | Requerido para descubrir nodos/pods | El descubrimiento parte de métricas, no solo de listas de recursos |
| Destino de Tentacle | Requerido para enviar datos | Accesible desde el servidor de Discovery |
| Versiones concretas de OpenShift, Pandora FMS o sistema operativo | Sin validar | No se establece compatibilidad por versión ni resultados de pruebas reales |

Obtenga el paquete `.disco` de la [entrada de OpenShift del Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.openshift) y cárguelo como aplicación de Discovery. Seleccione la aplicación denominada **Openshift** en su definición de paquete. Esta tarea no utiliza el ejecutable `oc`, inicio de sesión CLI ni parámetro de proyecto.

Solicite al administrador del clúster acceso a la API y confirmación de que hay métricas de nodos/pods. Debe autorizar las consultas indicadas; el rol y la preparación local del clúster de la antigua guía CLI no constituyen una política de acceso validada para esta aplicación.

### Seguridad de conexión

Las peticiones directas usan HTTPS **sin verificar el certificado**, por lo que no autentican la identidad del servidor. Restrinja el acceso de red. La tarea guarda el token en su archivo de configuración generado; proteja el acceso a la tarea y al archivo. Para ejecución manual, use un archivo protegido, no un token en argumentos del comando.

Con **Use proxy**, las peticiones usan **Proxy url** sin cabecera Bearer. La URL del proxy debe incluir esquema. El paquete no configura un tiempo de espera para las peticiones; los retrasos de red pueden bloquear la recopilación.

## Configurar la tarea de Discovery

Defina nombre, servidor de ejecución, grupo de agentes e intervalo en Discovery. Todos los agentes generados heredan grupo e intervalo. El paquete define los pasos **Openshift base** y **Openshift detailed**. La referencia completa de campos figura al final.

1. En **Openshift base**, indique **Openshift host** sin esquema, **Openshift port** y **Openshift token** para acceso directo. Para acceso por proxy, active **Use proxy** e indique **Proxy url** en su lugar.
2. Configure **Tentacle IP** y **Tentacle port** para recibir el XML; sus valores predeterminados son `127.0.0.1` y `41121`.
3. En **Openshift detailed**, seleccione **Scan Deployments**, **Scan Nodes** y **Scan Pods**. Todos están activados de forma predeterminada.
4. Ejecute la tarea y revise la información de ejecución y los agentes generados.

El asistente no tiene controles de filtro de namespaces, prefijos, salud, componentes, operadores ni imagestreams. Los tres interruptores controlan la generación de agentes de recursos; las consultas de métricas, deployments y globales siguen ejecutándose aunque se desactiven.

<!-- SCREENSHOT NEEDED: Pasos base y detailed de OpenShift Discovery 1.0, sin credenciales, para validar la interfaz renderizada de esta versión. -->

## Verificar la primera ejecución

1. Revise el resumen de Discovery: **Total agents**, **Nodes agents**, **Pods agents** y **Deployments agents** cuentan agentes generados. No confirman la entrega por Tentacle.
2. Compruebe el global **Openshift** y las categorías habilitadas. Los agentes de nodo/pod requieren datos completos de métricas, recursos asignables, nodo e IP. Los deployments requieren una condición `Available` o `Progressing` con estado `True`.
3. Contraste réplicas y valores representativos de CPU/memoria con el clúster. Los porcentajes usan los recursos asignables del nodo, no los requests ni límites del contenedor.
4. Revise errores antes de interpretar agentes o módulos ausentes como ausencia de recursos. Una ejecución parcial puede generar agentes y presentar fallos.

**No interprete `API status = 1` como prueba de conectividad:** el paquete asigna siempre ese valor. Revise módulos de salud y errores de petición. Asimismo, `Available` de deployment siempre vale `0` en los deployments generados por este paquete; compruebe disponibilidad real con réplicas y condiciones del clúster.

No se ha ejecutado la integración en un clúster ni instalado el paquete para esta documentación. El ejemplo manual siguiente no se ha ejecutado.

## Interpretar los resultados

### Agentes e identidad

| Agente | Alias | Padre |
| --- | --- | --- |
| Global | `Openshift` | Ninguno |
| Nodo | `<NODE_NAME>` | `Openshift` |
| Deployment | `<DEPLOYMENT_NAME>` | `Openshift` |
| Pod | `<POD_NAME>` | Su nodo |

La tarea no expone un prefijo. La configuración manual acepta `prefix`, que se antepone a alias e identidades. Los nodos apuntan entonces al global con prefijo y los pods al nodo con prefijo; los deployments siguen apuntando a `Openshift` sin prefijo. Los agentes de pod usan la IP del pod como dirección.

Las identidades de pod y deployment omiten el namespace. Los nombres iguales entre namespaces pueden colisionar; sin prefijo, también pueden colisionar entre clústeres. Esta aplicación no tiene filtro de namespaces. Cambiar el prefijo manual cambia las identidades generadas; sigue aplicándose la limitación del padre de deployments.

### Resumen funcional

| Agente | Resultados |
| --- | --- |
| Global | Salud, recuentos y listas de servicios/namespaces, componentes, recuentos y listas de estado de replication controllers y servicios de API, recuento de deployments |
| Nodo | Pods recopilados y porcentaje de capacidad, CPU/memoria y condiciones del nodo |
| Deployment | Réplicas deseadas, actualizadas, listas, disponibles y no disponibles; módulos `Available` y `Progressing` con las limitaciones siguientes |
| Pod | Fase, un módulo de condición, número de contenedores y CPU/memoria por contenedor |

Los agentes de nodo parten de métricas de nodo; los de pod, de métricas de pod. Los datos incompletos pueden interrumpir una fase completa y dejar salida parcial. `Pods` del nodo cuenta los pods procesados con métricas, no un recuento independiente validado de todos los pods planificados.

Las condiciones del nodo **no se normalizan a saludable = 1**: cada condición vale `1` para estado `True` y `0` en otro caso, incluidas las de presión. La salida del pod contiene solo la **última condición devuelta**, no un módulo por condición. Compruebe el nombre del módulo antes de interpretar su valor.

## Operar

### Ejecución manual

Use el ejecutable distribuido con un archivo protegido de líneas `key=value`:

```bash
pandora_openshift --conf <PATH_TO_CONFIG>
```

Sustituya todos los marcadores de este ejemplo directo no ejecutado:

```ini
ip=<TARGET_HOST>
port=<API_PORT>
token=<API_TOKEN>
agents_group_name=<AGENT_GROUP>
interval=300
transfer_mode=tentacle
tentacle_ip=<TENTACLE_HOST>
tentacle_port=41121
use_proxy=0
deployments=1
nodes=1
pods=1
```

La ejecución produce JSON de Discovery con contadores de generación y crea/transfiere XML de agentes. Un resumen ilustrativo es `{"summary":{"Total agents":4,"Nodes agents":1,"Pods agents":1,"Deployments agents":1}}`. No aplique a este ejecutable los códigos numéricos de éxito/error del antiguo plugin de servidor. `-h`/`--help` muestra ayuda de argumentos.

## Solución de problemas

| Señal | Comprobación |
| --- | --- |
| `Error en la solicitud a <endpoint>: <status>` | Revise host, puerto, acceso al endpoint y estado HTTP. Para `401`/`403`, revise token y autorización para esa ruta exacta. El host directo no debe incluir esquema. |
| `Can't get metrics`, `Error: Nodes` o `Error: Pods` | Revise respuestas de métricas, CPU/memoria/pods asignables, nodos asignados, IP de pods y condiciones. Los campos ausentes pueden interrumpir recopilación o generación. |
| Faltan deployments o aparece `Error: Deployments` | Revise interruptor, datos devueltos y condición `Available`/`Progressing` con estado `True`. |
| `Available` vale `0` aunque el deployment esté disponible | Una limitación del paquete hace que este valor no sea fiable; use réplicas y condiciones del clúster. |
| `Progressing` vale `0` aunque esa condición sea `True` | Se selecciona la primera condición `Available`/`Progressing` con estado `True`. Una condición `Available` anterior tiene prioridad. |
| `API status` sigue a `1` con fallos de API | Es una constante, no una prueba de conectividad. Revise salud y errores. Las peticiones de salud fallidas omiten sus módulos. |
| Faltan módulos globales o aparece `Error: global_agent` | Revise cada petición y los datos de deployments. Los fallos de consultas globales opcionales pueden omitir grupos; otros datos incompletos pueden impedir transferir el global. |
| Solo aparece una condición de pod | Esta versión emite únicamente la última condición devuelta para el pod. |
| La recopilación se bloquea | No hay tiempo de espera HTTP configurado; revise conectividad y ejecución de la tarea. |
| Falla el proxy | Revise URL base completa y autenticación del proxy; la tarea no envía cabecera Bearer en este modo. |
| Se cuentan agentes que no se reciben | Revise conectividad con Tentacle; los contadores se incrementan antes del envío. |

## Referencia

### Campos de consola — Openshift base

| Nombre | Macro | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- | --- |
| Openshift host | `_ip_` | Modo directo | Vacío | Host de la API sin esquema |
| Openshift port | `_port_` | Modo directo | Vacío | Puerto numérico de API |
| Openshift token | `_token_` | Endpoints directos protegidos | Vacío | Token Bearer; el asistente permite dejarlo vacío |
| Use proxy | `_useProxy_` | No | off | Usa URL proxy sin cabecera Bearer |
| Proxy url | `_proxyUrl_` | Modo proxy | Vacío | URL base con esquema; visible con Use proxy |
| Tentacle IP | `_tentacleIP_` | Sí | `127.0.0.1` | Destino de XML |
| Tentacle port | `_tentaclePort_` | Sí | `41121` | Puerto numérico de envío |

### Campos de consola — Openshift detailed

| Nombre | Macro | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- | --- |
| Scan Deployments | `_scanDeployments_` | No | on | Genera agentes de deployment que cumplan las condiciones |
| Scan Nodes | `_scanNodes_` | No | on | Genera agentes de nodo a partir de las métricas |
| Scan Pods | `_scanPods_` | No | on | Genera agentes de pod a partir de las métricas |

### Archivo de configuración

Estos valores predeterminados corresponden a la ejecución manual salvo que se indiquen valores de tarea. Discovery proporciona automáticamente grupo, intervalo, transferencia y campos de consola. Los interruptores enteros de recursos/proxy usan `1` para activar y `0` para desactivar.

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ip` | Modo directo | Vacío | Host de API sin esquema |
| `port` | Modo directo | Vacío | Puerto de API |
| `token` | Endpoints directos protegidos | Vacío | Token Bearer; proteja el archivo |
| `use_proxy` | No | `0` | Usa proxy sin cabecera Bearer |
| `proxy_url` | Modo proxy | Vacío | URL base con esquema |
| `agents_group_name` | No | Vacío; grupo de tarea en Discovery | Grupo de agentes |
| `interval` | No | `300`; intervalo de tarea en Discovery | Intervalo de agentes en segundos |
| `prefix` | No | Vacío | Prefijo de identidad solo manual; no aparece en el asistente |
| `transfer_mode` | Para enviar | Vacío; `tentacle` en Discovery | Use `tentacle` para la transferencia documentada |
| `tentacle_ip` | Para Tentacle | Vacío; `127.0.0.1` en Discovery | Destino de envío |
| `tentacle_port` | No | `41121` | Puerto de envío |
| `deployments` | No | `1` | Genera agentes de deployment |
| `nodes` | No | `1` | Genera agentes de nodo |
| `pods` | No | `1` | Genera agentes de pod |
| `data_dir` | No | Vacío | Aceptada, pero no selecciona el directorio de salida XML |

### Módulos generados

#### Agente global

| Nombre | Tipo | Valor o condición |
| --- | --- | --- |
| `API status` | `generic_proc` | Constante `1`, no demuestra salud de API |
| Un módulo por endpoint de salud inferior | `generic_proc` | `1` si responde exactamente `ok`; `0` en otro caso; omitido si falla la petición |
| `Services count` | `generic_data` | Número de servicios devueltos |
| `List Services` | `generic_data_string` | Nombres de servicios |
| `Namespaces count` | `generic_data` | Número de namespaces devueltos |
| `List Namespaces` | `generic_data_string` | Nombres de namespaces |
| `Components` | `generic_data` | Número de estados de componentes |
| `<component>.<condition>` | `generic_proc` | `1` solo para estado exactamente `TRUE`; `0` en otro caso |
| `Replication Controllers count` | `generic_data` | Número de replication controllers devueltos |
| `Replication Controllers Status` | `generic_data_string` | Entradas `<name>.<namespace>.Status : <status>` |
| `APIServices count` | `generic_data` | Número de servicios de API registrados |
| `APIServices Status` | `generic_data_string` | Entradas `<name>.Status : <conditions>` |
| `Deployments` | `generic_data` | Número de deployments devueltos, independiente de interruptores de generación |

Los grupos de servicios, namespaces, componentes, replication controllers y servicios de API requieren una respuesta correcta de su consulta. Esta aplicación no genera los agentes de imagestreams, operadores, CSV ni estadísticas separadas de pods del antiguo plugin CLI.

#### Agentes de nodo

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Pods` | `generic_data` | — | Pods procesados en el nodo |
| `Pods (%)` | `generic_data` | `%` | Recuento dividido por capacidad asignable de pods, multiplicado por 100 |
| `CPU (cores)` | `generic_data` | `cores` | CPU utilizada por el nodo |
| `CPU (%)` | `generic_data` | `%` | Uso frente a CPU asignable del nodo |
| `Memory (bytes)` | `generic_data` | `bytes` | Memoria utilizada por el nodo |
| `Memory (%)` | `generic_data` | `%` | Uso frente a memoria asignable del nodo |
| Cada condición de nodo devuelta | `generic_proc` | — | `1` para `True`; `0` en otro caso; no invierte condiciones de presión |

#### Agentes de deployment

Solo se generan si una condición `Available` o `Progressing` tiene estado `True`; la primera coincidencia determina el estado seleccionado.

| Nombre | Tipo | Valor |
| --- | --- | --- |
| `Replicas` | `generic_data` | Réplicas deseadas |
| `Updated replicas` | `generic_data` | Réplicas actualizadas; `0` si falta |
| `Ready replicas` | `generic_data` | Réplicas listas; `0` si falta |
| `Available replicas` | `generic_data` | Réplicas disponibles; `0` si falta |
| `Unavailable replicas` | `generic_data` | Réplicas no disponibles; `0` si falta |
| `Available` | `async_proc` | Siempre `0` en este paquete; no interpretar como disponibilidad real |
| `Progressing` | `async_proc` | `1` si el estado seleccionado es `Progressing`; `0` en otro caso |

Esta aplicación no genera módulos `Age` ni `Ready` de deployment.

#### Agentes de pod

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Pod status` | `generic_data` | — | `0` Failed, `1` Running, `2` Succeeded, `3` Pending, `4` Unknown/otro |
| Última condición de pod devuelta | `generic_proc` | — | Para `PodScheduled`, `Ready`, `Initialized`, `ContainersReady`: `1` para `True`; para `Unschedulable`: `1` para `False`; en otro caso `0`. Las condiciones no reconocidas no se interpretan de forma fiable |
| `Containers` | `generic_data` | — | Contenedores en las métricas recopiladas del pod |
| `Container <name> CPU (cores)` | `generic_data` | `cores` | CPU del contenedor, cuando se calcula |
| `Container <name> CPU (%)` | `generic_data` | `%` | Uso frente a CPU asignable de su nodo, cuando se calcula |
| `Container <name> memory (bytes)` | `generic_data` | `bytes` | Memoria del contenedor, cuando se calcula |
| `Container <name> memory (%)` | `generic_data` | `%` | Uso frente a memoria asignable de su nodo, cuando se calcula |

### Peticiones a la API

Son las consultas realizadas, no un rol validado. Las consultas globales no tienen interruptores independientes.

| Recurso | Ruta GET |
| --- | --- |
| Detalles de nodo | `/api/v1/nodes/<NODE_NAME>` |
| Métricas de nodo | `/apis/metrics.k8s.io/v1beta1/nodes` |
| Pods | `/api/v1/pods` |
| Métricas de pod | `/apis/metrics.k8s.io/v1beta1/pods` |
| Deployments | `/apis/apps/v1/deployments` |
| Servicios | `/api/v1/services` |
| Namespaces | `/api/v1/namespaces` |
| Estados de componentes | `/api/v1/componentstatuses` |
| Replication controllers | `/api/v1/replicationcontrollers` |
| Servicios de API registrados | `/apis/apiregistration.k8s.io/v1/apiservices` |

| Nombre del módulo de salud | Ruta GET |
| --- | --- |
| `healthz` | `/healthz` |
| `healthzPing` | `/healthz/ping` |
| `healthzLog` | `/healthz/log` |
| `healthzEtcd` | `/healthz/etcd` |
| `healthzPoststarthook crd informer synced` | `/healthz/poststarthook/crd-informer-synced` |
| `healthzPoststarthook generic apiserver start informers` | `/healthz/poststarthook/generic-apiserver-start-informers` |
| `healthzPoststarthook start apiextensions controllers` | `/healthz/poststarthook/start-apiextensions-controllers` |
| `healthzPoststarthook start apiextensions informers` | `/healthz/poststarthook/start-apiextensions-informers` |
