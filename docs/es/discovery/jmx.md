# JMX Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery JMX monitoriza aplicaciones Java mediante Java Management Extensions (JMX). Se conecta al endpoint JMX de cada objetivo configurado, lee los atributos de los MBeans que elija y los convierte en agentes y módulos de Pandora FMS.

Una tarea de Discovery genera **un agente por cada objetivo JMX**. Cada agente contiene un módulo por cada atributo de MBean recogido. Puede elegir qué se recoge de dos formas, combinables:

- **MBeans seleccionados en la consola.** La consola se conecta a un endpoint JMX de referencia y muestra los MBeans que expone. Se recogen todos los atributos de cada MBean seleccionado, en todos los objetivos de la tarea.
- **Métricas personalizadas.** Una lista explícita de entradas `MBean/atributo`, con umbrales opcionales.

La misma selección se aplica a todos los objetivos de una tarea, así que agrupe en una tarea solo objetivos que expongan los mismos MBeans.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.jmx`, versión `1.2` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Un entorno de ejecución de Java disponible en el servidor de Pandora FMS que ejecuta la tarea | `Requerido` | El addon inicia una máquina virtual Java para abrir las conexiones JMX |
| Acceso de red desde el servidor de Discovery a cada endpoint JMX | `Requerido` | El addon abre una conexión JMX por cada objetivo |
| Versiones de Java, fabricantes de Java y servidores de aplicaciones | `No validado` | No se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor de Discovery | `No validado` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `No validado` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Un entorno de ejecución de Java** instalado en el servidor de Pandora FMS que ejecuta la tarea de Discovery, disponible para el usuario que la ejecuta.
2. **JMX remoto habilitado en cada aplicación Java monitorizada**, alcanzable desde el servidor de Discovery. Consulte [Habilitar JMX remoto](#habilitar-jmx-remoto).
3. **La URL de servicio JMX de cada objetivo**, por ejemplo `service:jmx:rmi:///jndi/rmi://<TARGET_HOST>:<JMX_PORT>/jmxrmi`.
4. **Credenciales JMX**, solo cuando el objetivo requiera autenticación.

### Habilitar JMX remoto

La aplicación monitorizada no necesita software adicional, pero debe iniciarse con las opciones de la JVM que habilitan JMX remoto. El siguiente conjunto lo habilita en el host local sin autenticación ni TLS y está pensado solo para un entorno de pruebas:

```text
-Dcom.sun.management.jmxremote
-Dcom.sun.management.jmxremote.authenticate=false
-Dcom.sun.management.jmxremote.ssl=false
-Dcom.sun.management.jmxremote.port=<JMX_PORT>
-Dcom.sun.management.jmxremote.rmi.port=<JMX_PORT>
-Djava.rmi.server.hostname=localhost
```

Para exigir autenticación, defina `-Dcom.sun.management.jmxremote.authenticate=true` y añada los ficheros de contraseñas y de acceso:

```text
-Dcom.sun.management.jmxremote.password.file=<PATH_TO_PASSWORD_FILE>
-Dcom.sun.management.jmxremote.access.file=<PATH_TO_ACCESS_FILE>
```

Para conectar desde otro host, `java.rmi.server.hostname` debe ser una dirección alcanzable por el servidor de Discovery. Las opciones exactas para su aplicación y la protección del fichero de contraseñas las define la aplicación Java, no este addon.

### Gestión de credenciales

- El usuario y la contraseña introducidos en la tarea se almacenan con la definición de la tarea y se envían al servidor JMX como credenciales JMX.
- Mientras la consola carga la lista de MBeans, pasa el usuario y la contraseña como argumentos al ejecutable auxiliar, por lo que pueden ser visibles en la lista de procesos del servidor de Pandora FMS durante esa operación.
- Un fichero de configuración usado en la [ejecución manual](#ejecucion-manual) contiene la contraseña en texto claro. Protéjalo con permisos restrictivos.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.jmx](https://marketplace.pandorafms.com/entries/pandorafms.jmx)

Cárguelo en Pandora FMS. Una vez cargado, **JMX** está disponible en la sección **Applications** al crear tareas de Discovery.

El addon incluye sus propios ejecutables, `bin/pandora_jmx` y `bin/get_jmx_tree`.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones de Discovery y elija **JMX**. La consola presenta los campos en tres pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **JMX Basic** — objetivos y credenciales:

    - **Instances target strings**: los objetivos a monitorizar, uno o varios por línea, separados por comas. Cada objetivo es una URL de servicio JMX, seguida opcionalmente de `|` y del nombre de agente que se usará. Las líneas que empiezan por `#` se ignoran.
    - **JMX Url**: el endpoint de referencia, usado solo para listar los MBeans disponibles en el paso siguiente. No define un objetivo.
    - **Auth basic**, **User** y **Password**: credenciales para las conexiones JMX. Usuario y contraseña se muestran al activar **Auth basic**.

    ![Paso JMX Basic del asistente con el objetivo, JMX Url y los campos de autenticación](../assets/images/discovery/jmx/jmx-wizard-basic.png)

2. **JMX Mbeans** — un árbol de los MBeans que expone el endpoint de **JMX Url**, leído con las credenciales del paso anterior. Seleccione los MBeans que quiera recoger. Se recogen todos los atributos de cada MBean seleccionado en todos los objetivos.

    ![Paso JMX Mbeans del asistente con el árbol de MBeans disponibles](../assets/images/discovery/jmx/jmx-wizard-mbeans-tree.png)

3. **JMX detailed** — opciones de ejecución, nombres y filtrado:

    - **Max threads**: número de objetivos procesados en paralelo.
    - **Use prefix for modules** y **Use prefix for agents**: prefijos añadidos a los nombres de módulos y agentes generados.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: destino de los datos de agente generados. Rara vez hay que cambiarlos.
    - **Regexp to filter modules** y **Regexp to discard modules**: conservan o descartan métricas mediante una expresión regular.
    - **Custom Metrics**: entradas `MBean/atributo` explícitas con umbrales opcionales.
    - **Rename default modules** y **Modules names**: asignan nombres de módulo propios.

    ![Paso JMX detailed del asistente: Max threads y prefijos](../assets/images/discovery/jmx/jmx-wizard-detailed-prefixes.png)

    ![Paso JMX detailed del asistente: campos de Tentacle y de expresiones regulares](../assets/images/discovery/jmx/jmx-wizard-detailed-tentacle-regexp.png)

    ![Paso JMX detailed del asistente: Custom Metrics y nombres de módulos](../assets/images/discovery/jmx/jmx-wizard-detailed-metrics-names.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

### Métricas personalizadas

Escriba una métrica por línea con el formato `<MBean>/<atributo>`, seguida opcionalmente de umbrales separados por `|`. Cada umbral es una palabra clave y un valor separados por un espacio. Las líneas que empiezan por `#` y las líneas vacías se ignoran.

```text
java.lang:type=Threading/ThreadCount
java.lang:type=Threading/TotalStartedThreadCount|min_warning 30|min_critical 45
java.lang:type=Memory/HeapMemoryUsage/used
```

- Los umbrales que admite el addon son `min_warning`, `max_warning`, `min_critical` y `max_critical`.
- Para leer un campo de un atributo compuesto, añada su nombre tras el atributo, como en `java.lang:type=Memory/HeapMemoryUsage/used`.
- Si referencia un atributo compuesto sin campo, se crea un módulo por cada uno de sus campos; los umbrales no se aplican a esos módulos.

### Renombrar módulos

Los nombres de módulo son por defecto `<MBean>/<atributo>`, por ejemplo `java.lang:type=Threading/ThreadCount`. Para sustituir un nombre, escriba en **Modules names** una línea con el nombre original, un `|` y el nombre nuevo:

```text
java.lang:type=Threading/ThreadCount | Threads.count
```

El nombre original debe coincidir exactamente con el nombre por defecto, sin el prefijo de módulo. Si **Use prefix for modules** está activado, el prefijo se añade después del renombrado.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que se completa informa de **Total agents**, el número de agentes generados. Los errores y avisos se registran en la información de ejecución de la tarea.

    ![Resumen de la tarea con Total agents](../assets/images/discovery/jmx/jmx-task-summary.png)

2. **Los agentes.** Uno por objetivo, en el grupo de la tarea. El alias del agente es el nombre de agente indicado tras `|` en el objetivo, o la URL de servicio JMX si no se indica ninguno, con el prefijo de agente cuando esté configurado.

3. **Los módulos.** Uno por atributo recogido. Compruebe que aparecen los atributos que seleccionó o incluyó como métricas personalizadas y que tienen valor.

    ![Módulos generados a partir del MBean java.lang:type=Threading](../assets/images/discovery/jmx/jmx-threading-modules.png)

## Comprender los resultados

### Agentes generados

| Elemento | Valor |
|----------|-------|
| Agentes | Uno por cada objetivo de **Instances target strings** |
| Alias | El texto tras `|` en el objetivo, o el propio objetivo si no lo hay; precedido por el prefijo de agente cuando esté configurado |
| Nombre de agente | Un identificador derivado del alias, incluido el prefijo. El mismo alias reporta al mismo agente entre ejecuciones y tareas |
| Descripción | `Created by JMX plugin` |
| Grupo e intervalo | El grupo y el intervalo de la tarea de Discovery |

Cambiar el nombre de agente o el prefijo de agente de un objetivo crea un agente distinto, así que manténgalos estables para conservar el histórico.

### Módulos generados

Cada atributo recogido produce un módulo. Su tipo depende del valor leído:

| Valor leído | Tipo de módulo | Valor |
|-------------|----------------|-------|
| Número entero, long, float o double | `generic_data` | El número |
| Booleano | `generic_proc` | `1` para verdadero y `0` para falso |
| Cualquier otro valor | `generic_data_string` | El valor como texto |

No se crea un módulo cuyo valor de texto sea `True` o `False`. Los atributos que no se pueden leer, porque no existen en un objetivo o no están disponibles, producen un aviso en la información de ejecución y ningún módulo.

Los atributos de los MBeans seleccionados se filtran con las expresiones regulares de la tarea; las métricas personalizadas también se filtran con ellas. Los umbrales de las métricas personalizadas se establecen en el módulo generado.

## Operar

### Ejecución manual

El addon se puede ejecutar fuera de una tarea de Discovery con tres ficheros:

```bash
./pandora_jmx --conf <PATH_TO_CONFIG> --target_instances <PATH_TO_TARGETS> [--target_metrics <PATH_TO_METRICS>]
```

- `--conf`: fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion). Obligatorio.
- `--target_instances`: los objetivos, con el mismo formato que **Instances target strings**. Obligatorio.
- `--target_metrics`: las métricas personalizadas, con el mismo formato que **Custom Metrics**. Opcional.

Imprime un documento JSON con el resumen (`Total agents`) y, cuando hay mensajes, un campo `info`, y envía un fichero de datos por agente con Tentacle. El código de salida es `1` cuando no se puede leer el fichero de configuración o el de objetivos.

### Ajuste de la ejecución

**Max threads** (`threads`) es el número de procesos de trabajo. Cada proceso toma objetivos de una cola compartida, así que más procesos que objetivos no aportan beneficio. Cada proceso inicia su propia máquina virtual Java, que consume memoria en el servidor de Pandora FMS.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es la información de ejecución de la tarea (el campo `info` en la ejecución manual).

- **`Failed to connect: <error>`**: falló la conexión con un objetivo. Compruebe la URL de servicio JMX, la ruta de red, el puerto JMX y las credenciales, y que la aplicación se inició con JMX remoto habilitado.
- **`Failed processing <url>: <error>`**: se produjo un error al recoger un objetivo.
- **`[WARNING] Failed to read attributes from <MBean>: <error>`**: no se pudo leer un MBean seleccionado en un objetivo, por ejemplo porque no existe en él.
- **`[WARNING] Could not read '<attribute>' from MBean '<MBean>'`**: el atributo no existe, es transitorio o no se puede leer. No se crea el módulo.
- **`Database targets not defined`**: **Instances target strings** está vacío o solo contiene comentarios. La tarea no genera agentes.
- **`Error while parsing configuration zones or instances: <error>`**: el valor de `jmx_mbeans` no es una lista JSON válida (ejecución manual).
- **`Failed to read custom attributes: <error>`** y **`Failed to parsing module names: <error>`**: no se pudieron leer las métricas personalizadas o los nombres de módulos.
- **No aparecen MBeans en el segundo paso**: compruebe la **JMX Url**, las credenciales y la ruta de red desde el servidor de Pandora FMS hasta ese endpoint.
- **Menos módulos de los esperados**: revise las expresiones regulares; una métrica que no coincide con **Allow regexp**, o que coincide con **Deny regexp**, no se crea.

## Referencia

### Parámetros de la tarea

#### JMX Basic

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Instances target strings | `_targetstrings_` | área de texto | — | Uno o varios objetivos por línea, separados por comas. Cada objetivo es una URL de servicio JMX, seguida opcionalmente de `\|<nombre de agente>`. Las líneas que empiezan por `#` se ignoran |
| JMX Url | `_jmxUrl_` | cadena | — | Endpoint de referencia usado para listar los MBeans en el paso siguiente |
| Auth basic | `_authBasic_` | casilla | desactivada | Muestra **User** y **Password** |
| User | `_user_` | cadena | — | Opcional. Se muestra con **Auth basic** activado |
| Password | `_password_` | contraseña | — | Opcional. Se muestra con **Auth basic** activado |

#### JMX Mbeans

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| JMX available Mbeans | `_jmxMbeans_` | árbol | ninguno | MBeans que expone **JMX Url**. Opcional. Los nombres con comillas dobles se muestran con comillas simples |

#### JMX detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Max threads | `_threads_` | número | `1` | Opcional. Procesos de trabajo |
| Use prefix for modules | `_usePrefixModules_` | casilla | desactivada | Muestra **Prefix for modules created** |
| Prefix for modules created | `_prefixModules_` | cadena | vacío | Opcional. Se añade a cada nombre de módulo |
| Use prefix for agents | `_usePrefixAgents_` | casilla | desactivada | Muestra **Prefix for agents created** |
| Prefix for agents created | `_prefixAgents_` | cadena | vacío | Opcional. Se añade a cada alias de agente y forma parte de su identidad |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos del agente |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | vacío | Opcional. La tarea lo acepta, pero esta versión no lo pasa al cliente de Tentacle |
| Regexp to filter modules | `_regexpFilter_` | casilla | desactivada | Muestra **Allow regexp** |
| Allow regexp | `_allowRegexp_` | cadena | vacío | Opcional. Solo se crean las métricas que coinciden con la expresión |
| Regexp to discard modules | `_regexpDiscard_` | casilla | desactivada | Muestra **Deny regexp** |
| Deny regexp | `_denyRegexp_` | cadena | vacío | Opcional. No se crean las métricas que coinciden con la expresión |
| Custom Metrics | `_customMetrics_` | área de texto | Una guía comentada con un ejemplo | Opcional. Consulte [Métricas personalizadas](#metricas-personalizadas) |
| Rename default modules | `_renameModules_` | casilla | activada | Muestra **Modules names** |
| Modules names | `_ModulesNames_` | área de texto | vacío | Opcional. Un `nombre original\|nombre nuevo` por línea |

Las expresiones regulares se buscan en cualquier parte del texto (no están ancladas). Se aplican al nombre `<MBean>/<atributo>` de cada atributo de los MBeans seleccionados y a cada línea completa de las métricas personalizadas, umbrales incluidos.

### Fichero de configuración

Se usa en la ejecución manual. Tiene una sección `[CONF]` y una sección opcional `[MODULE_NAMES]`. Los valores son pares `clave = valor`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `jmx_url` | vacío | Endpoint de referencia. Se lee por compatibilidad con la tarea; los objetivos proceden de `--target_instances` |
| `user` | vacío | Usuario JMX |
| `password` | vacío | Contraseña JMX |
| `jmx_mbeans` | `[]` | Lista JSON de nombres de MBean cuyos atributos se recogen todos, por ejemplo `["java.lang:type=Threading","java.lang:type=ClassLoading"]` |
| `module_prefix` | vacío | Prefijo de los nombres de módulo |
| `agent_prefix` | vacío | Prefijo de los alias de agente |
| `agents_group_name` | `jmx` | Grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos. Un valor que no es un número se lee como `0` |
| `threads` | `4` | Procesos de trabajo. Un valor que no es un número se lee como `0` |
| `transfer_mode` | `tentacle` | `local` escribe los ficheros de datos localmente; cualquier otro valor los envía con Tentacle |
| `tentacle_client` | `tentacle_client` | Ejecutable del cliente de Tentacle |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `tentacle_opts` | vacío | Se acepta, no se pasa al cliente de Tentacle en esta versión |
| `data_dir` | `/var/spool/pandora/data_in/` | Se acepta por compatibilidad con los demás addons de Discovery |
| `temporal` | `/tmp` | Se acepta por compatibilidad con los demás addons de Discovery |
| `allow_regexp` | vacío | Solo se crean las métricas que coinciden |
| `deny_regexp` | vacío | No se crean las métricas que coinciden |

La sección `[MODULE_NAMES]` contiene un `nombre original | nombre nuevo` por línea.

Ejemplo:

```ini
[CONF]
user = <USERNAME>
password = <PASSWORD>
jmx_url = service:jmx:rmi:///jndi/rmi://<TARGET_HOST>:<JMX_PORT>/jmxrmi
module_prefix = app.
agent_prefix = app.
agents_group_name = jmx
interval = 300
threads = 2
transfer_mode = tentacle
tentacle_ip = <TENTACLE_SERVER_IP>
tentacle_port = 41121
allow_regexp =
deny_regexp =
jmx_mbeans = ["java.lang:type=Threading","java.lang:type=ClassLoading"]

[MODULE_NAMES]
java.lang:type=Threading/ThreadCount | Threads.count
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | JMX |
| Identificador | `pandorafms.jmx` |
| Versión | `1.2` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.jmx](https://marketplace.pandorafms.com/entries/pandorafms.jmx), paquete actual actualizado el 2026-06-22 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
