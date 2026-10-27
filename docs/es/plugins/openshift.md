# Plugin de monitorización Pandora Openshift

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Pandora Openshift monitoriza un clúster de OpenShift desde Pandora FMS
ejecutando el cliente de línea de comandos de OpenShift (`oc`) en el host donde
corre el plugin. En cada ejecución inicia sesión con un usuario y una
contraseña, selecciona un proyecto, lee objetos del clúster y del proyecto y
construye agentes de Pandora FMS a partir de la salida de los comandos: un
agente por nodo, pod y deployment, un agente por grupo de recursos y un agente
resumen con el número de elementos.

Cada ejecución entrega los agentes por sí misma, como documentos `agent_data`,
mediante el cliente de Tentacle o en una carpeta de datos local. El plugin no
imprime módulos para que los recoja un agente de Pandora FMS, así que se usa
como plugin de servidor o desde un planificador, nunca como plugin de agente.

Esta página documenta el addon **`pandorafms.openshift_plugin`**, el plugin de
monitorización basado en la CLI. El **Discovery** de OpenShift
(`pandorafms.openshift`) es otro addon: se ejecuta desde el asistente de tareas
de Discovery, habla con la API del clúster con un token y genera sus agentes
desde la tarea. No usa `oc`, ni un proyecto, ni estos archivos de configuración.
Consulte [OpenShift Discovery](../discovery/openshift.md).

## Preparación

### Compatibilidad y disponibilidad

| Alcance | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.openshift_plugin`, versión `1.0` | Objetivo documentado | Versión de la entrada del Marketplace y del propio plugin. Véase [Identidad del addon](#identidad-del-addon) |
| El cliente `oc` en el host donde corre el plugin | `Requerido` | Cada paso de la recolección es un comando `oc`; `cli` nombra el binario |
| Acceso de red desde ese host al endpoint de la API de OpenShift | `Requerido` | `oc login` y todos los comandos llegan a la API indicada en `ip` |
| Una cuenta de OpenShift con lectura en todo el clúster y acceso al proyecto | `Requerido` | Los comandos de [Comandos de `oc`](#comandos-de-la-cli-de-openshift) son de ámbito de clúster y de proyecto; véase [Requisitos](#requisitos) |
| La API de métricas de OpenShift | `Requerido` para métricas de nodo y de pod | Los datos de CPU y memoria de los nodos y el agente de estadísticas de pods vienen de `oc adm top nodes` y `oc adm top pods` |
| `tentacle_client` en `PATH` | `Requerido` cuando `mode=tentacle` (el valor distribuido) | La entrega ejecuta el cliente de Tentacle |
| Una `local_folder` con permiso de escritura | `Requerido` cuando `mode` no es `tentacle` | La entrega copia el XML en esa carpeta |
| CentOS 7 y Fedora como sistema del host | `Compatible conocido` | La edición anterior de esta guía registra esos sistemas como los que se probaron; no se ha revalidado para la versión `1.0` |
| Otros sistemas del host | `Sin validar` | No hay otro sistema registrado. El plugin necesita un cliente `oc` y un cliente de Tentacle para la plataforma del host |
| Versiones de OpenShift | `Sin validar` | No hay matriz de versiones registrada. El plugin llama a `oc get cs`, una API que Kubernetes declaró obsoleta y que los clústeres recientes pueden no servir |
| Versiones de Pandora FMS | `Sin validar` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y posteriores; no hay una declaración específica de este addon |

La entrada del Marketplace recomienda explorar los plugins alternativos de su
biblioteca para obtener las últimas funciones y soporte.

### Requisitos

1. **El cliente `oc` en el host donde corre el plugin**, en una versión capaz de
   hablar con el clúster de destino. El plugin ejecuta el binario indicado en
   `cli`; no aplica ninguna ruta por defecto ni comprueba que el archivo exista.
2. **Acceso de red al endpoint de la API de OpenShift** desde ese host,
   normalmente en el puerto TCP `6443`. `ip` debe ser la URL de la API que
   acepta `oc login`, con esquema y puerto, por ejemplo
   `https://<TARGET_HOST>:6443`.
3. **Una cuenta de OpenShift** capaz de ejecutar los comandos de lectura de este
   plugin. Las lecturas de nodos, namespaces, servicios de API, estados de
   componente y operadores de clúster son de ámbito de clúster; las de pods,
   deployments, servicios, controladores de replicación, imagestreams y versiones
   de servicio de clúster se limitan al proyecto seleccionado. La edición anterior
   de esta guía recomienda el rol `cluster-reader`; no se ha validado un rol más
   restrictivo para este plugin.
4. **La API de métricas de OpenShift** habilitada en el proyecto y en el
   clúster, para que `oc adm top nodes` y `oc adm top pods` devuelvan filas.
5. **Pandora FMS** para recibir los agentes: el servidor de Pandora FMS, ya sea
   mediante su servidor de Tentacle o mediante una carpeta de datos que lea.
6. **El cliente de Tentacle (`tentacle_client`) en `PATH`**, cuando la entrega
   usa Tentacle.

### Instalar y registrar el plugin

El paquete del Marketplace es `pandorafms.openshift_plugin.1.0.pspz2`. Incluye
el plugin, un archivo de configuración y la definición de registro que lee la
consola:

| Archivo | Destino tras el registro |
| --- | --- |
| `pandora_openshift.pl` | `<attachment_store>/plugin/pandora_openshift.pl` |
| `pandora_openshift.conf` | `<attachment_store>/plugin/pandora_openshift.conf` |
| `plugin_definition.ini` | La consola lo lee y lo elimina en el registro |

Para registrarlo, abra **Servers → Register plugin** en la consola de Pandora
FMS, seleccione el archivo `.pspz2` y pulse **Upload file**. La consola registra
un plugin llamado **Pandora Openshift** con una sola macro, `_field1_`, cuyo
valor por defecto es la ruta del archivo de configuración. Los valores del
registro están en
[Registrar el paquete en la consola](#registrar-el-paquete-en-la-consola).

La ruta por defecto registrada supone el directorio de adjuntos
predeterminado, `/var/www/html/pandora_console/attachment`. Si la instalación
usa otro `attachment_store`, edite el valor de la macro con la ruta real.

El archivo de configuración distribuido no puede recolectar nada: no tiene ruta
de `oc`, ni credenciales, ni host de Tentacle, y su proyecto y su prefijo son
`prueba`. Edite el archivo de configuración en el servidor que ejecuta el
plugin antes de la primera ejecución, como se describe en
[Configuración](#configuracion).

El plugin también puede registrarse a mano desde **Servers → Plugins** con
**Add plugin**, usando **Plugin command**
`<attachment_store>/plugin/pandora_openshift.pl` y los parámetros
` _field1_ `.

<!-- SCREENSHOT NEEDED: Página "Register plugin" de la consola de Pandora FMS con el .pspz2 de OpenShift seleccionado en el formulario de subida y sin hosts ni cuentas reales. -->

### Credenciales y seguridad de la conexión

- El usuario y la contraseña de OpenShift se guardan en texto plano en el
  archivo de configuración. El registro extrae todos los archivos del paquete
  con modo `0755`, así que el archivo de configuración queda legible por
  cualquier usuario local hasta que lo restrinja. Póngalo en `chmod 600` y con
  el propietario del proceso del servidor de Pandora FMS.
- Cada ejecución lanza `oc login -u <USERNAME> -p <PASSWORD> <IP>`. La
  contraseña aparece por tanto en la línea de comandos del proceso `oc` y
  cualquier usuario local puede leerla en la lista de procesos mientras dura el
  inicio de sesión. Este plugin no ofrece ninguna vía de entrada sin contraseña.
- `oc login` guarda la sesión en el kubeconfig del usuario que ejecuta el
  plugin, normalmente `$HOME/.kube/config`. El plugin no lo borra, así que el
  token permanece en disco entre ejecuciones.
- El plugin no pasa ninguna opción de TLS a `oc`, de modo que `oc` verifica el
  certificado de la API con sus valores por defecto. Con un certificado
  autofirmado, haga que el host confíe en la CA del clúster; en caso contrario
  el inicio de sesión falla y todos los colectores devuelven vacío.
- El plugin no lee la salida de error de `oc`. Los mensajes, como un fallo de
  autenticación, van a la salida de error de la ejecución y no la detienen.

## Configuración

### Archivo de configuración

El archivo de configuración es un archivo de texto con líneas `clave=valor`.
Las líneas que empiezan por `#` y las líneas en blanco se omiten, las claves y
los valores se recortan y la última aparición de una clave repetida prevalece.
El archivo no tiene secciones.

Pase el archivo como primer argumento del plugin:

```bash
pandora_openshift.pl <PATH_TO_CONFIG>
```

El plugin no aplica valores por defecto propios más allá de los del archivo
distribuido y no valida nada: una clave ausente se comporta como un valor vacío,
lo que desactiva el paso o la entrega correspondiente. Esta es una
configuración completa con marcadores:

```ini
# cliente oc
cli=/usr/local/bin/oc
user=<USERNAME>
password=<PASSWORD>
ip=https://<TARGET_HOST>:6443
project=<PROJECT>

# entrega
mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER>
tentacle_port=41121

# colectores
prefix=<PREFIX>
as_server_plugin=1
agent_openshift=1
agent_node=1
agent_pod=1
agent_pod_stats=1
agent_deployment=1
agent_imagestreams=1
agent_apiservice=1
agent_services=1
agent_replication_controller=1
agent_component_status=1
agent_operators=1
agent_csv=0
top_imagestreams_count=11
```

Todas las claves se describen en
[Claves del archivo de configuración](#claves-del-archivo-de-configuracion).

### Alcance del proyecto y colectores

La ejecución empieza con `oc login` y después `oc project <PROJECT>`. El
proyecto delimita el alcance de los pods, deployments, servicios, controladores
de replicación, imagestreams y versiones de servicio de clúster que lee el
plugin; los nodos, namespaces, servicios de API, estados de componente y
operadores de clúster se leen en todo el clúster. Una ejecución monitoriza un
proyecto más los objetos de ámbito de clúster, así que para monitorizar varios
proyectos use varias ejecuciones del plugin con valores de `prefix` distintos.

Las claves `agent_*` activan o desactivan colectores. `1` activa un colector y
`0` lo desactiva; cualquier otro valor también lo desactiva. En el archivo
distribuido están activos todos los colectores salvo `agent_csv`.

`prefix` se antepone a todos los nombres de agente. En el archivo distribuido es
`prueba`; con un valor vacío los nombres de agente empiezan por el guion bajo,
por ejemplo `_OS_POD_<POD_NAME>`.

## Verificación

Ejecute el plugin a mano en el host que lo ejecuta, pasando el archivo de
configuración como único argumento:

```bash
pandora_openshift.pl <PATH_TO_CONFIG>
```

El plugin se registra como ejecutable; `perl pandora_openshift.pl
<PATH_TO_CONFIG>` produce el mismo resultado. Con `as_server_plugin=1` (el valor
distribuido), una ejecución completa imprime un único entero y termina:

| Salida | Significado |
| --- | --- |
| `11` | Los once bloques activos terminaron y se entregaron. Es el valor con los interruptores distribuidos, donde `agent_csv=0` |
| `12` | Terminaron los doce bloques, incluido el colector de versiones de servicio de clúster (`agent_csv=1`) |
| Un número menor | Terminaron todos los bloques contados; el número es el total de bloques activos, así que baja al desactivar colectores |
| `0` | No se ejecutó ningún colector: todos los interruptores están desactivados o no se cargó ningún archivo de configuración |

El número impreso cuenta bloques entregados, no datos recolectados. Un bloque
cuyo comando `oc` no devolvió filas también termina, así que una ejecución puede
imprimir `11` y producir agentes sin módulos.

Un bloque que falla no imprime número: el plugin se detiene en ese bloque y
termina con estado `0`. Use `as_server_plugin=0` para ver qué bloque falló, como
se describe en [Lectura de fallos](#lectura-de-fallos).

Tras una ejecución correcta, confirme en Pandora FMS que existen los agentes
indicados en [Agentes](#agentes) con sus módulos. La entrega por Tentacle exige
que el host alcance `tentacle_ip:tentacle_port`; el puerto por defecto es
`41121`.

<!-- SCREENSHOT NEEDED: Lista de agentes de la consola de Pandora FMS con los agentes <prefix>_Openshift y <prefix>_OS_* creados por este plugin, sin nombres de host de clientes. -->

## Entender los resultados

### Agentes

| Agente | Se crea a partir de | Módulos |
| --- | --- | --- |
| `<prefix>_Openshift` | Recuentos de elementos de siete comandos `oc` | Siete contadores |
| `<prefix>_OS_Nodo_<NODE_NAME>` | Filas de `oc adm top nodes` | Estado del nodo, condiciones, asignación y CPU/memoria |
| `<prefix>_OS_POD_<POD_NAME>` | Filas de `oc get pods` | `Ready`, `Status`, `Restarts`, `Age` |
| `<prefix>_OS_POD_Stats` | Filas de `oc adm top pods` | Dos módulos por pod |
| `<prefix>_OS_DEPLOYMENT_<DEPLOYMENT_NAME>` | Filas de `oc get deployments` | `Ready`, `Up to date`, `Avalaible`, `Age` |
| `<prefix>_OS_Imagestreams` | Filas de `oc adm top imagestreams` | Dos módulos por imagestream |
| `<prefix>_OS_Api_service` | Filas de `oc get apiservice` | Un módulo por servicio de API |
| `<prefix>_OS_Services` | Filas de `oc get services` | Un módulo por servicio |
| `<prefix>_OS_Replication_Controllers` | Filas de `oc get rc -o wide` | Cuatro módulos por controlador de replicación |
| `<prefix>_Component_status` | Filas `etcd` de `oc get cs` | Un módulo de disponibilidad por componente |
| `<prefix>_Cluster_operator` | Filas de `oc get co` | Un módulo de disponibilidad por operador |
| `<prefix>_Cluster_service_version` | Filas de `oc get csv` | Un módulo de fase por versión de servicio de clúster; desactivado por defecto |

Los agentes por nodo, por pod y por deployment existen solo mientras su comando
`oc` devuelve filas. Los agentes agrupados se entregan aunque el comando no
devuelva nada, así que un agente sin módulos significa que el comando no produjo
filas, no que el plugin haya fallado.

### Valores

- Solo los contadores del resumen, las comprobaciones de condición y las
  comprobaciones de clúster son numéricos: `generic_data` para los contadores y
  `generic_proc` para las comprobaciones. Todos los valores por recurso son
  módulos `generic_data_string` que guardan el texto que imprimió `oc`, de modo
  que valores como `2/2`, `120m`, `10Gi` o `2d` no admiten umbrales numéricos.
- Los siete contadores del resumen son recuentos de líneas de la salida del
  comando sin la línea de cabecera. Un comando `oc` que falla no produce líneas
  y por tanto publica `0`; el plugin no distingue un proyecto vacío de un
  comando fallido.
- El módulo contador de servicios se llama `Services ` — el nombre termina en un
  espacio, algo fácil de pasar por alto al buscarlo en la consola.
- El módulo de disponibilidad de los deployments se llama `Avalaible`, con esa
  ortografía. Su valor es la columna `AVAILABLE` de `oc get deployments`.
- `MemoryPressure`, `DiskPressure` y `PIDPressure` informan `1` cuando
  `oc describe node` devuelve `False` para la condición, es decir, cuando no hay
  presión. `Ready` informa `1` cuando el estado es `True`.
- `oc get cs` devuelve las filas de componentes etcd solo para los componentes
  cuyo nombre contiene `etcd`. Un clúster cuya API ya no sirve el recurso
  `componentstatuses` no produce filas y el agente se entrega sin módulos.
- `Allocated cpu` y `Allocated memory` no son el porcentaje de asignación. El
  plugin toma el cuarto token separado por espacios de la fila `cpu` o `memory`
  del bloque **Allocated resources** del nodo, que en el formato estándar de
  `oc describe node` es el valor absoluto de la columna **Limits**, le quita sus
  dos últimos caracteres y después el primero, y compara el resto con 80 y 90.
  Con el formato habitual el resultado es un número alterado y ambos módulos
  informan normalmente `1`.

### Los agentes de nodo

El colector de nodos se comporta de forma distinta al resto:

- Los documentos por nodo se construyen con `oc get nodes` y seis llamadas a
  `oc describe node` por nodo, pero esa primera pasada no se entrega.
- Los agentes entregados proceden de `oc adm top nodes`. La lista de módulos no
  se reinicia entre los nodos de la primera pasada, así que el agente de la
  **primera** fila de `oc adm top nodes` recibe los módulos `Status`, `Roles`,
  `Age`, `Version`, de condición y `Allocated` de **todos** los nodos, con los
  mismos nombres de módulo repetidos una vez por nodo, más sus cuatro métricas
  de `adm top`.
- El resto de agentes de nodo recibe solo `Cpu (cores)`, `Cpu %`, `Memory` y
  `Memory %`.

En un clúster de un solo nodo el primer agente lleva el inventario completo del
nodo. En un clúster de varios nodos sus módulos de inventario mezclan varios
nodos y no se pueden atribuir a uno concreto, así que consulte el estado de los
nodos con `oc get nodes` o en los módulos de CPU y memoria del resto de agentes
de nodo.

## Operación y diagnóstico

### Ejecución y programación

- Una ejecución es puntual: inicia sesión, recolecta, entrega y termina. No
  guarda estado salvo el kubeconfig que escribe `oc login`.
- Programe el plugin desde un módulo de plugin en Pandora FMS, o desde `cron`
  cuando entregue en una carpeta local. Cada ejecución recolecta el estado del
  clúster en ese momento.
- El paquete registrado fija un tiempo máximo de `20` segundos. Una ejecución
  arranca un proceso `oc` nuevo para el inicio de sesión, el cambio de proyecto,
  los recuentos y cada colector, y el colector de nodos lanza seis comandos
  `oc describe node` por nodo. Un clúster con muchos nodos puede superar ese
  tiempo máximo; auméntelo al registrar o editar el plugin.
- Active `debug=1` para que los errores de entrega se impriman en la salida de
  error. Sin él, una transferencia de Tentacle fallida o una copia local fallida
  son silenciosas.

### Lectura de fallos

Con `as_server_plugin=0`, un bloque que falla imprime un módulo XML en la salida
estándar en lugar del resultado numérico:

```xml
<module>
	<name><![CDATA[Pandora_Openshift]]></name>
	<type>generic_proc</type>
	<data><![CDATA[0]]></data>
	<description><![CDATA[Nodes node-01]]></description>
</module>
```

La descripción nombra el bloque y el recurso que falló: `Nodes <nodo>`,
`Pods <pod>`, `Pods stats`, `Deployments <deployment>`, `Imagestreams`,
`Api service`, `Services`, `Replication Controllers`, `Component status`,
`Cluster operator`, `Cluster service version` u `Openshift Agent`. El bloque
global usa el nombre `<prefix>_Pandora_Openshift` en lugar de
`Pandora_Openshift`.

`as_server_plugin=0` no imprime los módulos recolectados: en una ejecución
correcta la salida estándar queda vacía. El plugin siempre entrega sus agentes
por sí mismo, así que no se puede usar como plugin de agente mediante
`module_plugin`.

La ejecución termina con estado `0` tanto si entregó todo como si no entregó
nada. No use el estado de salida para detectar un fallo.

### Limitaciones

- El resultado del inicio de sesión no se comprueba nunca. Con credenciales
  incorrectas, una API inalcanzable o un certificado no confiable, todos los
  comandos devuelven vacío y el plugin publica agentes con contadores a `0` y
  sin módulos de recurso, terminando igualmente con `0`.
- El plugin lee un proyecto por ejecución. No hay lista de namespaces, filtro ni
  modo multiproyecto.
- Solo se publica el detalle de módulo que imprime `oc`. El plugin no define
  umbrales, alertas ni transformaciones de métricas propias.
- `agent_csv` está desactivado en el archivo distribuido y `oc get csv` requiere
  el Operator Lifecycle Manager.

### Diagnóstico

| Señal | Comprobación |
| --- | --- |
| Una ejecución imprime `0` | No se activó ningún colector o no se leyó ningún archivo de configuración. Compruebe que `_field1_` apunta a un archivo existente y que las claves `agent_*` valen `1` |
| Una ejecución no imprime nada y termina con estado `0` | Un bloque no pudo entregar. Repita con `as_server_plugin=0` para obtener el bloque que falla y con `debug=1` para ver el error de entrega |
| `ERROR: [transfer_mode] set to [tentacle], but no [tentacle_ip] provided.` en la salida estándar | `mode=tentacle` no tiene `tentacle_ip`. El mensaje no detiene la ejecución; todas las entregas fallan después |
| Los agentes aparecen con contadores a `0` y sin módulos de recurso | Fallaron el inicio de sesión o los permisos. Ejecute `oc login` y los comandos de [Comandos de `oc`](#comandos-de-la-cli-de-openshift) con el mismo usuario y proyecto en el mismo host |
| Los agentes de nodo aparecen solo con cuatro módulos | Comportamiento normal en un clúster de varios nodos; véase [Los agentes de nodo](#los-agentes-de-nodo) |
| `Allocated cpu` y `Allocated memory` siempre valen `1` | Comportamiento de análisis documentado; los módulos no miden la asignación. Véase [Valores](#valores) |
| `<prefix>_OS_POD_Stats` no tiene módulos | La API de métricas no respondió a `oc adm top pods`. Compruebe el servidor de métricas y el proyecto |
| `<prefix>_Component_status` no tiene módulos | `oc get cs` no devolvió filas `etcd`, o el clúster ya no sirve `componentstatuses` |
| No hay agentes de nodo ni de pod | `agent_node` o `agent_pod` están desactivados, o el comando `oc` correspondiente no devolvió filas |
| Los agentes se entregan pero no aparecen en Pandora FMS | Compruebe `tentacle_ip`, `tentacle_port` y el servidor de Tentacle, o que `local_folder` exista y tenga permiso de escritura para el usuario del plugin |
| El tiempo máximo del plugin corta la ejecución | Aumente el tiempo máximo del plugin; véase [Ejecución y programación](#ejecucion-y-programacion) |

## Referencia

### Registrar el paquete en la consola

La definición de registro del paquete `.pspz2` fija estos valores:

| Campo | Valor |
| --- | --- |
| Nombre del plugin | `Pandora Openshift` |
| Descripción | `Plugin to monitor a Openshift environment using Openshift CLI` |
| Tipo de plugin | `Standard` |
| Tiempo máximo | `20` segundos |
| Comando del plugin | `<attachment_store>/plugin/pandora_openshift.pl` |
| Parámetros del plugin | ` _field1_ ` |

El paquete define una macro:

| Macro | Obligatoria | Valor por defecto | Ocultar | Descripción y ayuda |
| --- | --- | --- | --- | --- |
| `_field1_` | Sí, según su descripción | `/var/www/html/pandora_console/attachment/plugin/pandora_openshift.conf` | No | `Conf path (obligatory)`. Ayuda: `Path to conf file` |

`Ocultar` está desactivado, así que la consola muestra el campo como texto
plano. La consola no valida la macro: un valor vacío o incorrecto deja la
ejecución sin archivo de configuración y no recolecta nada.

<!-- SCREENSHOT NEEDED: Formulario de módulo de plugin en la consola de Pandora FMS con el campo de ruta de configuración _field1_ de este plugin, sin hosts ni credenciales reales. -->

### Claves del archivo de configuración

| Clave | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `cli` | Sí | Vacío | Ruta del binario `oc` en el host que ejecuta el plugin |
| `user` | Sí | Vacío | Nombre de usuario de OpenShift |
| `password` | Sí | Vacío | Contraseña de ese usuario, en texto plano |
| `ip` | Sí | Vacío | URL de la API que acepta `oc login`, con esquema y puerto, por ejemplo `https://<TARGET_HOST>:6443` |
| `project` | Sí | `prueba` | Proyecto seleccionado con `oc project`; delimita pods, deployments, servicios, controladores de replicación e imagestreams |
| `prefix` | No | `prueba` | Prefijo de todos los nombres de agente |
| `mode` | No | Vacío | Modo de entrega. `tentacle` usa el cliente de Tentacle; cualquier otro valor copia el XML en `local_folder`. Vacío sin `local_folder` no entrega nada |
| `transfer_mode` | No | Vacío | Alias de `mode`, usado solo cuando `mode` está vacío |
| `tentacle_ip` | Sí con `mode=tentacle` | Vacío | Dirección del servidor de Tentacle |
| `tentacle_port` | No | `41121` | Puerto del servidor de Tentacle |
| `tentacle_client` | No | `tentacle_client` | Nombre o ruta del ejecutable del cliente de Tentacle |
| `tentacle_opts` | No | Vacío | Opciones adicionales que se pasan al cliente de Tentacle |
| `local_folder` | Sí cuando `mode` no es `tentacle` | Vacío | Carpeta que recibe los archivos `agent_data`, por ejemplo una bandeja de datos de Pandora FMS |
| `tmp` | No | `/tmp` | Carpeta donde se escribe el XML antes de la entrega |
| `as_server_plugin` | No | `1` | `1` imprime el recuento de bloques y suprime el módulo de error por bloque; `0` imprime el módulo de error del bloque que falla |
| `as_agent_plugin` | No | Vacío | Alias que pone `as_server_plugin` a `0` cuando está activo y `as_server_plugin` no está definido |
| `debug` | No | Vacío | `1` imprime los errores de entrega en la salida de error |
| `module_group` | No | Vacío | Grupo de módulos asignado a todos los módulos generados |
| `module_interval` | No | Vacío | Intervalo de módulo asignado a todos los módulos generados, en segundos |
| `top_imagestreams_count` | No | `11` | Número de líneas de salida de `oc adm top imagestreams` que se pasan al analizador, cabecera incluida, así que produce como máximo un imagestream menos |
| `agent_openshift` | No | `1` | Agente de contadores del resumen |
| `agent_node` | No | `1` | Agentes por nodo |
| `agent_pod` | No | `1` | Agentes por pod |
| `agent_pod_stats` | No | `1` | Agente de estadísticas de pods |
| `agent_deployment` | No | `1` | Agentes por deployment |
| `agent_imagestreams` | No | `1` | Agente de imagestreams |
| `agent_apiservice` | No | `1` | Agente de servicios de API |
| `agent_services` | No | `1` | Agente de servicios |
| `agent_replication_controller` | No | `1` | Agente de controladores de replicación |
| `agent_component_status` | No | `1` | Agente de estados de componente |
| `agent_operators` | No | `1` | Agente de operadores de clúster |
| `agent_csv` | No | `0` | Agente de versiones de servicio de clúster |

Los valores por defecto de esta tabla son los del archivo de configuración
distribuido. Una clave ausente del archivo se comporta como un valor vacío, así
que omitir una clave no equivale a ponerla a `1`.

### Bloques del colector y valor de resultado

El plugin ejecuta sus colectores en este orden fijo. El número de resultado que
imprime con `as_server_plugin=1` es el total de bloques activos que terminaron.

| # | Interruptor | Comando | Agente |
| --- | --- | --- | --- |
| 1 | `agent_node` | `oc get nodes`, `oc describe node` (seis veces por nodo), `oc adm top nodes` | `<prefix>_OS_Nodo_<NODE_NAME>` |
| 2 | `agent_pod` | `oc get pods` | `<prefix>_OS_POD_<POD_NAME>` |
| 3 | `agent_pod_stats` | `oc adm top pods` | `<prefix>_OS_POD_Stats` |
| 4 | `agent_deployment` | `oc get deployments` | `<prefix>_OS_DEPLOYMENT_<DEPLOYMENT_NAME>` |
| 5 | `agent_imagestreams` | `oc adm top imagestreams` | `<prefix>_OS_Imagestreams` |
| 6 | `agent_apiservice` | `oc get apiservice` | `<prefix>_OS_Api_service` |
| 7 | `agent_services` | `oc get services` | `<prefix>_OS_Services` |
| 8 | `agent_replication_controller` | `oc get rc -o wide` | `<prefix>_OS_Replication_Controllers` |
| 9 | `agent_component_status` | `oc get cs --no-headers`, filtrado con `grep etcd` | `<prefix>_Component_status` |
| 10 | `agent_operators` | `oc get co --no-headers` | `<prefix>_Cluster_operator` |
| 11 | `agent_csv` | `oc get csv` con selección de columnas de nombre y fase | `<prefix>_Cluster_service_version` |
| 12 | `agent_openshift` | Siete comandos de recuento | `<prefix>_Openshift` |

Un bloque que no puede entregar detiene la ejecución antes de incrementar su
recuento, así que un fallo nunca produce un número.

### Módulos generados

#### Agente de resumen

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `Services ` | `generic_data` | Recuento de líneas de `oc get services` |
| `Deployments` | `generic_data` | Recuento de líneas de `oc get deployments` |
| `Namespaces` | `generic_data` | Recuento de líneas de `oc get namespaces` |
| `Nodes` | `generic_data` | Recuento de líneas de `oc get nodes` |
| `Pods` | `generic_data` | Recuento de líneas de `oc get pods` |
| `Imagestreams` | `generic_data` | Recuento de líneas de `oc adm top imagestreams`, sin el límite de `top_imagestreams_count` |
| `Replication controllers` | `generic_data` | Recuento de líneas de `oc get rc` |

#### Agentes de nodo

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `Status`, `Roles`, `Age`, `Version` | `generic_data_string` | Columnas de `oc get nodes`; véase [Los agentes de nodo](#los-agentes-de-nodo) |
| `MemoryPressure`, `DiskPressure`, `PIDPressure` | `generic_proc` | `1` cuando el estado de la condición es `False` |
| `Ready` | `generic_proc` | `1` cuando el estado de la condición es `True` |
| `Allocated memory`, `Allocated cpu` | `generic_proc` | `1` por debajo de 80, `2` de 80 a 90, `3` por encima de 90, sobre un valor que no mide la asignación |
| `Cpu (cores)`, `Cpu %`, `Memory`, `Memory %` | `generic_data_string` | Columnas de `oc adm top nodes` |

#### Agentes de pod

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `Ready` | `generic_data_string` | Columna `READY`, por ejemplo `1/1` |
| `Status` | `generic_data_string` | Columna `STATUS` |
| `Restarts` | `generic_data_string` | Columna `RESTARTS` |
| `Age` | `generic_data_string` | Columna `AGE` |

#### Agente de estadísticas de pods

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<POD_NAME>_Cpu (cores)` | `generic_data_string` | Columna `CPU(cores)` |
| `<POD_NAME>_Memory (bytes)` | `generic_data_string` | Columna `MEMORY(bytes)` |

#### Agentes de deployment

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `Ready` | `generic_data_string` | Columna `READY`, por ejemplo `2/2` |
| `Up to date` | `generic_data_string` | Columna `UP-TO-DATE` |
| `Avalaible` | `generic_data_string` | Columna `AVAILABLE` |
| `Age` | `generic_data_string` | Columna `AGE` |

#### Agente de imagestreams

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<IMAGESTREAM_NAME>_Storage` | `generic_data_string` | Columna `STORAGE` |
| `<IMAGESTREAM_NAME>_Images` | `generic_data_string` | Columna `IMAGES` |

#### Agente de servicios de API

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<API_SERVICE_NAME>` | `generic_data_string` | Columna `AVAILABLE`; la descripción lleva las columnas de servicio y antigüedad |

#### Agente de servicios

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<SERVICE_NAME>` | `generic_data_string` | Columna `PORT(S)`; la descripción lleva el tipo, la IP de clúster y la IP externa |

#### Agente de controladores de replicación

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<RC_NAME>_Ready` | `generic_data_string` | Columna `READY` |
| `<RC_NAME>_Desired` | `generic_data_string` | Columna `DESIRED` |
| `<RC_NAME>_Current` | `generic_data_string` | Columna `CURRENT` |
| `<RC_NAME>_Age` | `generic_data_string` | Columna `AGE`; la descripción lleva contenedores, imágenes y selector |

#### Agente de estados de componente

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<COMPONENT_NAME>` | `generic_proc` | `1` para `Healthy`, `0` en otro caso |

#### Agente de operadores de clúster

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<OPERATOR_NAME>` | `generic_proc` | `1` cuando la columna `AVAILABLE` es `True`, `0` en otro caso, incluido `Unknown` |

#### Agente de versiones de servicio de clúster

| Módulo | Tipo | Valor |
| --- | --- | --- |
| `<CSV_NAME>` | `generic_proc` | `1` cuando la fase es `Succeeded`, `0` en otro caso |

### Comandos de la CLI de OpenShift

| Comando | Ámbito | Uso |
| --- | --- | --- |
| `oc login -u <USERNAME> -p <PASSWORD> <IP>` | — | Sesión, una vez por ejecución |
| `oc project <PROJECT>` | — | Selecciona el proyecto |
| `oc get nodes` | Clúster | Inventario de nodos y contador `Nodes` |
| `oc describe node <NODE_NAME>` | Clúster | Condiciones y módulos `Allocated`, seis veces por nodo |
| `oc adm top nodes` | Clúster | Módulos de CPU y memoria de los nodos |
| `oc get pods` | Proyecto | Agentes de pod y contador `Pods` |
| `oc adm top pods` | Proyecto | Agente de estadísticas de pods |
| `oc get deployments` | Proyecto | Agentes de deployment y contador `Deployments` |
| `oc adm top imagestreams` | Proyecto | Agente de imagestreams y contador `Imagestreams` |
| `oc get apiservice` | Clúster | Agente de servicios de API |
| `oc get services` | Proyecto | Agente de servicios y contador `Services ` |
| `oc get rc -o wide` | Proyecto | Agente de controladores de replicación |
| `oc get rc` | Proyecto | Contador `Replication controllers` |
| `oc get cs --no-headers`, filtrado con `grep etcd` | Clúster | Agente de estados de componente |
| `oc get co --no-headers` | Clúster | Agente de operadores de clúster |
| `oc get csv -o custom-columns=NAME:.metadata.name,PHASE:.status.phase --no-headers` | Proyecto | Agente de versiones de servicio de clúster |
| `oc get namespaces` | Clúster | Contador `Namespaces` |

### Identidad del addon

| Campo | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.openshift_plugin` |
| Nombre en el Marketplace | Pandora Openshift |
| Versión del addon | `1.0` |
| Última actualización en el Marketplace | 2025-06-26 |
| Paquete del Marketplace | `pandorafms.openshift_plugin.1.0.pspz2` |
| Licencia | One |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Tipo del Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de servidor: colector por CLI que entrega XML de agente |
| Ejecutable | `pandora_openshift.pl` |

[https://marketplace.pandorafms.com/entries/pandorafms.openshift_plugin](https://marketplace.pandorafms.com/entries/pandorafms.openshift_plugin)
