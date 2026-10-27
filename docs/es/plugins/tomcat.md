# Tomcat monitoring plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin monitoriza una instancia de Apache Tomcat desde Pandora FMS. En cada
ejecución se autentica contra la aplicación web Manager de Tomcat, lee el
documento de estado de conectores y JVM y el informe de información de la JVM, y
construye **un agente de Pandora FMS** cuyos módulos son las métricas
recogidas. Después entrega el documento del agente a Pandora FMS con Tentacle o
lo copia en una carpeta de datos local.

No se instala nada en el host de Tomcat: el plugin se ejecuta en un host que
pueda alcanzar la aplicación Manager y no guarda estado entre ejecuciones. Cada
ejecución vuelve a leer el estado actual.

El plugin es un comando autónomo que entrega su propio agente. No es un plugin
de agente y no imprime XML de módulos para que lo recoja un agente de Pandora
FMS; imprime `1` cuando una ejecución termina y `0` cuando se detiene con un
error. Consulte [Verificación](#verificacion) para saber qué demuestra y qué no
demuestra esa salida.

Hay dos lecturas que se configuran de forma independiente y cada una produce su
propio grupo de módulos:

- **Documento de estado** (`/manager/status/all?XML=true`): memoria libre, total
  y máxima de la JVM, además de los contadores de hilos y de peticiones de un
  conector.
- **Informe de información de la JVM** (`/manager/text/vminfo`): métricas de
  runtime, sistema operativo, hilos, carga de clases, compilación, recolectores
  de basura y pools de memoria de la JVM que ejecuta Tomcat.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.tomcat`, versión `1.0` | Objetivo documentado | Versión del paquete del Marketplace que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| La aplicación web Manager de Tomcat desplegada en `<TARGET_HOST>:<port>` | `Requerido` | Cada lectura es una petición HTTP a `/manager/status/all?XML=true` o a `/manager/text/vminfo` |
| Un usuario de Tomcat con el rol `manager-script` | `Requerido` | La aplicación Manager restringe `/manager/text/*` a ese rol y también lo admite en `/manager/status/*` |
| Acceso de red desde el host del plugin hasta el conector de Tomcat | `Requerido` | El plugin conecta desde el host donde se ejecuta |
| Acceso de red al puerto de Tentacle, `41121` por defecto | `Requerido` cuando la entrega no es una copia local | La entrega por Tentacle es la opción por defecto |
| Una carpeta `/var/spool/pandora/data_in/` escribible en el host del plugin | `Requerido` para la copia local | `transfer_mode=local` mueve el documento a esa carpeta |
| Versiones de Tomcat | `Sin validar` | No hay matriz de versiones registrada para la versión `1.0` |
| Sistema operativo del host del plugin | `Sin validar` | No hay sistema operativo registrado para la versión `1.0` |
| Pandora FMS NG 784 y posteriores | `Sin validar` | No existe un registro de validación por versión. El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |

### Requisitos

1. **Una instalación de Tomcat con la aplicación web Manager desplegada.** Cada
   lectura apunta a una ruta `/manager/...`, así que un Tomcat sin la aplicación
   Manager no se puede monitorizar con este plugin.
2. **Un usuario de Tomcat con el rol `manager-script`** en `tomcat-users.xml`,
   como se describe en [Crear el usuario de Tomcat](#crear-el-usuario-de-tomcat).
3. **Acceso de red** desde el host del plugin hasta el conector que atiende la
   aplicación Manager.
4. **Un destino para el agente generado**: el servicio Tentacle de Pandora FMS o
   una carpeta de datos local que lea el servidor de Pandora FMS.
5. **Un host para ejecutar el plugin.** Lo habitual es el propio servidor de
   Pandora FMS, porque desde ahí se entrega el agente.

### Crear el usuario de Tomcat

El plugin se autentica con HTTP Basic contra la aplicación Manager. Añada un
usuario con el rol `manager-script` al fichero de usuarios de Tomcat:

```xml
<tomcat-users>
  <role rolename="manager-script"/>
  <user username="<USERNAME>" password="<PASSWORD>" roles="manager-script"/>
</tomcat-users>
```

`manager-script` es el único rol que necesita el plugin: la aplicación Manager
asocia la interfaz `/text/*` a ese rol y también lo admite en la interfaz
`/status/*`. Aplique el cambio y reinicie Tomcat.

Las credenciales viajan en cada petición:

- Por HTTP sin cifrar, el usuario y la contraseña se envían sin cifrar, en una
  cabecera que solo va codificada. Use `https=1` cuando el camino entre el host
  del plugin y Tomcat no sea de confianza.
- La contraseña se guarda en el fichero de configuración del plugin en texto
  plano. Restrinja los permisos del fichero al usuario que ejecuta el plugin.

### Instalar el plugin

Descargue el addon desde la entrada del Marketplace de Pandora FMS, limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.tomcat](https://marketplace.pandorafms.com/entries/pandorafms.tomcat)

Instale el ejecutable en el host que lo vaya a ejecutar y mantenga su fichero de
configuración junto a él. El plugin toma ese fichero como único argumento, así
que cualquier ubicación es válida siempre que la ejecución use la misma ruta.
Dé al ejecutable permiso de ejecución.

## Configuración

El plugin toma una única opción, `--conf`, con la ruta de su fichero de
configuración:

```bash
./pandora_tomcat --conf <PATH_TO_CONFIG>
```

El fichero de configuración es un fichero INI con una única sección llamada
`CONF`. Sus valores sustituyen a los valores por defecto integrados. Se aplican
estas reglas:

- **La cabecera `[CONF]` es obligatoria.** Un fichero con solo líneas
  `clave=valor`, como usaba la generación anterior del addon, se rechaza: el
  plugin imprime el mensaje del analizador y `0`, y termina (consulte
  [Resolución de problemas](#resolucion-de-problemas)).
- **Solo se leen las claves dentro de `[CONF]`.** Una clave escrita fuera de la
  sección se ignora y se aplica su valor por defecto.
- **Una clave ausente conserva su valor por defecto.** El valor por defecto de
  cada clave está en [Fichero de configuración](#fichero-de-configuracion).
- **No escriba comentarios después de un valor.** Todo lo que sigue al `=` llega
  al plugin como parte del valor; use líneas completas que empiecen por `#` para
  los comentarios.
- **Una clave repetida conserva su último valor.**

Use `password`, no `pass`: el plugin solo lee la clave `password`. Las claves de
la generación anterior del addon — `pass`, `instance`, `custom_url`, `threads`,
`MODULE_GROUP`, `enable_thread_monitoring`, `enable_jvm_memory_monitoring` y el
resto — no se leen y no cambian nada.

### Conexión con Tomcat

```ini
[CONF]
host=<TARGET_HOST>
port=8080
user=<USERNAME>
password=<PASSWORD>
https=0
```

- `host` es un nombre de host o una dirección IP, sin esquema y sin puerto: el
  plugin construye él mismo `http://<host>:<port>/manager/...`, de modo que un
  valor como `http://<TARGET_HOST>` se toma como un host llamado `http` y la
  ejecución no conecta.
- `port` es el conector que sirve la aplicación Manager, `8080` por defecto. Un
  valor no numérico se lee como `0`.
- `https` cambia el esquema a `https` solo cuando su valor es exactamente `1`.
  Cualquier otro valor, incluido `true`, mantiene `http`.
- La ruta de contexto del Manager está fija en `/manager`. Un Tomcat cuya
  aplicación Manager esté desplegada en otra ruta no se puede configurar aquí.

### Elegir qué recoger

```ini
enable_status_monitoring=1
enable_vminfo_monitoring=1
```

Cada interruptor habilita su lectura solo cuando su valor es exactamente `1`;
`0`, `2`, un valor vacío o un valor no numérico lo deshabilitan. No se aplica la
regla de "cualquier valor mayor que cero" de otros addons.

- `enable_status_monitoring` recoge el documento de estado. Produce los tres
  módulos de memoria de la JVM y los módulos de hilos y de peticiones de un
  conector.
- `enable_vminfo_monitoring` recoge el informe de información de la JVM.

Con los dos interruptores deshabilitados el plugin sigue construyendo y
entregando un agente, pero el agente no tiene módulos.

### Filtrar los nombres de métrica

```ini
allow_regexp=
deny_regexp=
```

Ambos valores son expresiones regulares que se buscan en cualquier posición del
nombre de la métrica:

- `allow_regexp`: cuando no está vacío, solo se publican las métricas cuyo
  nombre contiene una coincidencia. `allow_regexp=bytes` conserva
  `bytesReceived` y `bytesSent` y descarta el resto.
- `deny_regexp`: se descartan las métricas cuyo nombre contiene una
  coincidencia.
- Ambos vacíos, el valor por defecto, no aplican ningún filtro.

Los filtros se aplican a las métricas de hilos y de peticiones del conector y a
las métricas de información de la JVM. No se aplican a `memory_free`,
`memory_total` ni `memory_max`.

### Identidad del agente

```ini
agent_name=Tomcat
agents_group_name=tomcat
interval=300
module_prefix=
```

- `agent_name` es el alias del agente generado. El nombre de agente que guarda
  Pandora FMS es un hash de 32 caracteres derivado de este valor, así que el
  texto configurado identifica el agente como alias y nunca como nombre. Cambiar
  `agent_name` cambia el hash y crea otro agente, y deja el anterior sin datos.
- `agents_group_name` es el grupo del agente, por nombre.
- `interval` es el intervalo del agente en segundos. Un valor no numérico se lee
  como `0`.
- `module_prefix` se antepone a todos los nombres de módulo sin separador, de
  modo que `module_prefix=tc01` convierte `maxThreads` en `tc01maxThreads`.
  Déjelo vacío salvo que haya que distinguir los módulos de varias instancias de
  Tomcat.

### Entrega a Pandora FMS

Tentacle es la opción por defecto. Necesita la dirección del servidor Tentacle:

```ini
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_URL>
tentacle_port=41121
```

La copia local escribe el documento en la carpeta de datos de Pandora FMS, que
es la opción habitual cuando el plugin se ejecuta en el propio servidor de
Pandora FMS:

```ini
transfer_mode=local
```

- `transfer_mode` selecciona la copia local solo cuando su valor es exactamente
  `local`. Cualquier otro valor, incluido el `tentacle` por defecto y una errata
  como `tentacle_`, entrega con el cliente Tentacle.
- El cliente Tentacle es el ejecutable `tentacle_client` que se encuentre en
  `PATH`. Los errores del cliente se escriben en la salida de error estándar.
- `temporal`, `data_dir`, `tentacle_client` y `tentacle_opts` se aceptan y se
  ignoran. El documento se escribe siempre en `/tmp`, la copia local va siempre a
  `/var/spool/pandora/data_in/` y no se pasan opciones adicionales a Tentacle.
  Cree `/var/spool/pandora/data_in/` antes de la primera ejecución local.

### Ejecutarlo desde Pandora FMS

El plugin entrega su propio agente, así que se ejecuta como comando programado en
un host, no como módulo de un agente de Pandora FMS:

- **Como plugin de servidor.** Registre el ejecutable en la consola como plugin
  de servidor estándar y pase `--conf <PATH_TO_CONFIG>` como parámetros. Pandora
  FMS lo ejecuta entonces en el servidor propietario del módulo, con el intervalo
  del plugin.
- **Como tarea programada.** Añada el comando al `cron` del host del plugin, como
  se describe en [Ejecución programada](#ejecucion-programada).

No lo registre como plugin de agente esperando XML de módulos: imprime `1` o `0`,
no módulos. Ejecutarlo desde un comando de agente produce ese único valor como
módulo, mientras que el agente de Tomcat se entrega por separado.

<!-- SCREENSHOT NEEDED: formulario de registro de plugin de servidor en Pandora FMS con la ruta al ejecutable pandora_tomcat y --conf <PATH_TO_CONFIG> como parámetros, sin nombres de host ni credenciales reales. -->

## Verificación

Ejecute el plugin manualmente desde un terminal, pasando el fichero de
configuración:

```bash
./pandora_tomcat --conf <PATH_TO_CONFIG>
```

Cada ejecución se hace una vez y termina.

- `1` en la salida estándar significa que la ejecución llegó al final sin una
  excepción. **No** demuestra que el agente haya llegado a Pandora FMS.
- `0` en la salida estándar significa que la ejecución se detuvo con un error
  que el plugin gestionó. El mensaje de error se imprime en la línea anterior al
  `0`.
- Un traceback en la salida de error estándar, sin `1` y sin `0`, significa que
  la ejecución se detuvo antes de entregar nada: no se pudo alcanzar la
  aplicación Manager, se rechazaron las credenciales o la respuesta no era el
  documento esperado.

Una ejecución sin argumentos, o con `--conf` y sin valor, imprime el resumen de
uso y termina con estado `2`. `-h` imprime el mismo resumen y termina con estado
`0`.

Después confirme la llegada en la consola: un agente con el `agent_name`
configurado como alias —su nombre guardado es el hash de 32 caracteres descrito
en [Identidad del agente](#identidad-del-agente)— y los módulos descritos en
[Entender los resultados](#entender-los-resultados) una vez transcurrido el
intervalo.

<!-- SCREENSHOT NEEDED: vista de detalle del agente Tomcat en Pandora FMS, con el alias configurado y los módulos de hilos y peticiones del conector con datos, sin nombres de host ni credenciales reales. -->

Una ejecución que imprime `1` tampoco demuestra que todas las recogidas hayan
funcionado: consulte
[Limitaciones conocidas de esta versión](#limitaciones-conocidas-de-esta-version).

## Entender los resultados

El plugin produce siempre **un agente**. Sus módulos se agrupan en cuatro
conjuntos:

- **Memoria de la JVM.** `memory_free`, `memory_total` y `memory_max` informan
  de los valores del elemento `<memory>` del documento de estado, en bytes. Su
  valor se escribe con llaves y comillas, así que en esta versión no sirven como
  números; consulte las limitaciones más abajo.
- **Hilos del conector.** Un módulo por atributo de la información de hilos del
  primer conector: `maxThreads`, `currentThreadCount` y `currentThreadsBusy` en
  un Tomcat actual.
- **Peticiones del conector.** Un módulo por atributo de la información de
  peticiones del primer conector: `maxTime`, `processingTime`, `requestCount`,
  `errorCount`, `bytesReceived` y `bytesSent`.
- **Información de la JVM.** Un módulo por línea del informe de información de la
  JVM que supera el filtro del plugin, con el nombre de la etiqueta de la línea y
  los espacios sustituidos por guiones bajos, por ejemplo `heap_used` o
  `availableprocessors`.

Todos los módulos se declaran como `generic_data`, incluidos los que llevan un
valor de texto, y ninguno lleva unidad, umbral ni grupo de módulos. Los valores
que describen bytes se publican, por tanto, como números sin unidad.

El agente se crea con el grupo y el intervalo configurados, el sistema operativo
vacío, la dirección vacía y la marca de tiempo de la ejecución. No tiene agente
padre.

## Operar y resolver problemas

### Ejecución programada

El plugin no tiene planificador propio, así que lo ejecuta uno externo: el
planificador de plugins de servidor de Pandora FMS o una entrada de `cron` en el
host del plugin:

```cron
*/5 * * * * root /usr/share/pandora_server/util/plugin/pandora_tomcat --conf <PATH_TO_CONFIG>
```

Ajuste la programación al intervalo del agente para que el agente reciba datos
con la cadencia que la consola espera para él.

### Comportamiento de la ejecución

- El plugin no guarda estado entre ejecuciones y se puede ejecutar a mano en
  cualquier momento.
- No fija ningún tiempo de espera en las peticiones. Una aplicación Manager que
  acepte la conexión y no responda nunca deja la ejecución esperando; acote la
  ejecución desde fuera cuando exista ese riesgo, por ejemplo ejecutando el
  comando a través de `timeout`.
- Cuando recibe `SIGTERM` imprime `Received SIGTERM signal. Cleaning up...` y
  termina con estado `0`. Una ejecución cortada así no se distingue de una
  completada por su estado de salida.

### Limitaciones conocidas de esta versión

- **Los tres módulos de memoria de la JVM llevan un valor envuelto.**
  `memory_free`, `memory_total` y `memory_max` se escriben como `{'<número>'}`,
  con llaves y comillas incluidas, en lugar de un número desnudo. Pandora FMS no
  puede leerlos como una serie numérica. Los módulos de conector y de
  información de la JVM no se ven afectados.
- **Solo se lee el primer conector.** El plugin toma el primer `<threadInfo>` y el
  primer `<requestInfo>` del documento de estado y nombra sus módulos solo por el
  atributo. En un Tomcat con varios conectores solo se recoge el que aparece
  primero, y los módulos no identifican a qué conector pertenecen.
- **El nombre del agente es un hash.** Pandora FMS guarda el agente con un hash
  de 32 caracteres y `agent_name` se envía como alias. Decida el nombre antes de
  la primera ejecución, porque cambiarlo crea otro agente.
- **`temporal`, `data_dir`, `tentacle_client` y `tentacle_opts` no hacen nada.**
  La carpeta de escritura es siempre `/tmp`, la copia local va siempre a
  `/var/spool/pandora/data_in/` y el cliente Tentacle es siempre el que está en
  `PATH`, sin opciones adicionales.
- **Los fallos de entrega no se reflejan en la salida.** Con Tentacle, una
  entrega fallida escribe el error del cliente en la salida de error estándar,
  borra el documento generado y aun así imprime `1`. Con la copia local, un fallo
  imprime el error y `0`.
- **El estado de salida no describe la ejecución.** `1` y `0` se imprimen en la
  salida estándar y el proceso termina con estado `0` en ambos casos. Solo
  difieren los errores de línea de comandos (estado `2`) y los fallos no
  gestionados de conexión, autenticación o análisis (estado `1` con un
  traceback).
- **La ruta del Manager está fija.** El plugin pide siempre `/manager/...`; no
  hay ajuste de URL personalizada.
- **HTTPS no permite omitir la validación del certificado.** Con `https=1` el
  certificado del conector de Tomcat debe ser de confianza para el host del
  plugin. No hay opción para saltarse la verificación, así que un certificado
  autofirmado detiene la ejecución.
- **Todos los módulos de información de la JVM son `generic_data`.** Los valores
  de texto como `vmname`, `vmversion` o `vmvendor` se envían como texto dentro de
  un módulo numérico, así que no se pueden leer como una serie.
- **Los nombres de información de la JVM se repiten.** El informe tiene un bloque
  por recolector de basura y por pool de memoria, y el plugin usa solo la
  etiqueta de la línea, así que nombres como `getcollectioncount`,
  `current_used` o `peak_max` aparecen una vez por recolector o pool en el mismo
  documento, sin forma de distinguirlos.
- **No hay módulos de aplicaciones, sesiones ni workers.** Esta versión solo lee
  los informes de estado y de información de la JVM. No consulta la lista de
  aplicaciones, así que no produce módulos de estado ni de sesiones por
  aplicación, ni totales `[workers]`, ni porcentaje de uso de hilos.

### Resolución de problemas

- **Un traceback que termina en un error de URL no válida que menciona `No host
  supplied`** — `host` está vacío. Falta la sección `[CONF]` o la clave `host`, o
  la ruta del fichero de configuración es incorrecta y se usaron los valores por
  defecto integrados.
- **El plugin imprime un mensaje del analizador y `0`, y no genera ningún
  módulo** — el fichero de configuración no tiene cabecera `[CONF]`. Añádala.
- **Un traceback que termina en un error de análisis XML** — la aplicación
  Manager respondió con algo que no es el documento de estado. Compruebe las
  credenciales, las claves `user` y `password`, y que la aplicación Manager esté
  desplegada. Una autenticación rechazada devuelve una página de error, no el
  documento.
- **Un traceback que termina en un error de conexión** — Tomcat no escucha en
  `host:port`, el puerto es incorrecto o `https` no coincide con el conector.
  Revise la configuración del conector de Tomcat.
- **Un traceback que termina en un error SSL** — `https=1` y el certificado no es
  de confianza para el host del plugin. Importe la CA en el almacén de confianza
  del host o sirva la aplicación Manager con un certificado de confianza.
- **Los tres módulos de memoria llevan valores `{'...'}`** — es lo esperado en
  esta versión; consulte las limitaciones anteriores. Use los módulos de conector
  y de información de la JVM para analizar la memoria.
- **Menos módulos de los esperados** — `enable_status_monitoring` o
  `enable_vminfo_monitoring` no vale exactamente `1`, o `allow_regexp` y
  `deny_regexp` están filtrando nombres. Compruebe ambas cosas.
- **Los módulos de hilos y de peticiones cubren un solo conector** — es lo
  esperado; el plugin lee solo el primer conector.
- **El agente no aparece en la consola después de una ejecución que imprimió
  `1`** — la entrega falló. Compruebe el cliente Tentacle en `PATH`,
  `tentacle_ip` y `tentacle_port`, o que `transfer_mode=local` se haya
  seleccionado realmente y que `/var/spool/pandora/data_in/` sea escribible.

## Referencia

### Fichero de configuración

El fichero se pasa con `--conf` y contiene líneas `clave=valor` dentro de una
sección `CONF`. Los valores del fichero sustituyen a los valores por defecto
integrados que se muestran abajo.

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `host` | Sí | Vacío | Nombre de host o dirección IP de Tomcat, sin esquema y sin puerto |
| `port` | No | `8080` | Puerto del conector que sirve la aplicación Manager; un valor no numérico se lee como `0` |
| `user` | Sí | Vacío | Usuario de Tomcat con el rol `manager-script` |
| `password` | Sí | Vacío | Contraseña de `user`, guardada en texto plano |
| `https` | No | `0` | Solo `1` consulta `https://`; cualquier otro valor consulta `http://` |
| `enable_status_monitoring` | No | `1` | Solo `1` recoge el documento de estado: memoria, hilos y peticiones del conector |
| `enable_vminfo_monitoring` | No | `1` | Solo `1` recoge el informe de información de la JVM |
| `allow_regexp` | No | Vacío | Expresión regular; solo se publican las métricas cuyo nombre contiene una coincidencia. No se aplica a los módulos de memoria |
| `deny_regexp` | No | Vacío | Expresión regular; se descartan las métricas cuyo nombre contiene una coincidencia. Mismo ámbito que `allow_regexp` |
| `agent_name` | No | `Tomcat` | Alias del agente generado; el nombre guardado es un hash de 32 caracteres de este valor |
| `agents_group_name` | No | `tomcat` | Grupo del agente generado, por nombre |
| `interval` | No | `300` | Intervalo del agente en segundos; un valor no numérico se lee como `0` |
| `module_prefix` | No | Vacío | Texto que se antepone a todos los nombres de módulo, sin separador |
| `transfer_mode` | No | `tentacle` | Solo `local` copia el documento en `/var/spool/pandora/data_in/`; cualquier otro valor entrega con Tentacle |
| `tentacle_ip` | No | `127.0.0.1` | Dirección del servidor Tentacle; se usa salvo con `transfer_mode=local` |
| `tentacle_port` | No | `41121` | Puerto del servidor Tentacle |
| `temporal` | No | — | Se acepta y se ignora; el documento se escribe siempre en `/tmp` |
| `data_dir` | No | — | Se acepta y se ignora; la copia local va siempre a `/var/spool/pandora/data_in/` |
| `tentacle_client` | No | — | Se acepta y se ignora; el cliente es siempre `tentacle_client` de `PATH` |
| `tentacle_opts` | No | — | Se acepta y se ignora; no se pasan opciones adicionales a Tentacle |

### Ejecución por línea de comandos

```bash
./pandora_tomcat --conf <PATH_TO_CONFIG>
```

| Condición | Comportamiento |
| --- | --- |
| Sin argumentos, o `--conf` sin valor | El resumen de uso en la salida de error estándar y estado de salida `2` |
| `-h` o `--help` | El resumen de uso y estado de salida `0` |
| `--conf` apunta a un fichero legible con sección `[CONF]` | La ejecución usa esa configuración |
| `--conf` apunta a un fichero que no existe | El fichero se ignora, se aplican los valores por defecto y la ejecución se detiene con un error de URL no válida, estado de salida `1` |
| El fichero no tiene sección `[CONF]` | El mensaje del analizador y `0` en la salida estándar, estado de salida `0` |
| La ejecución llega al final | `1`, o `0` tras un error gestionado, y estado de salida `0` |
| La petición al Manager falla o su respuesta no se puede analizar | Un traceback en la salida de error estándar y estado de salida `1` |
| Se recibe `SIGTERM` | `Received SIGTERM signal. Cleaning up...` y estado de salida `0` |

### Módulos generados

Todos los módulos se declaran como `generic_data`, no llevan unidad y reciben el
valor de `module_prefix` delante del nombre. Las descripciones que escribe el
plugin son `Metrics type: JVM` para los módulos de memoria, `Metrics type:
THREADS` para los de hilos, `Metrics type: REQUESTS` para los de peticiones y
`Metrics type: VMINFO` para los de información de la JVM.

#### Módulos de memoria de la JVM

| Módulo | Cuándo | Significado |
| --- | --- | --- |
| `memory_free` | `enable_status_monitoring=1` | Memoria libre informada por la JVM, en bytes, envuelta como `{'<número>'}` |
| `memory_total` | `enable_status_monitoring=1` | Memoria total informada por la JVM, en bytes, envuelta como `{'<número>'}` |
| `memory_max` | `enable_status_monitoring=1` | Memoria máxima informada por la JVM, en bytes, envuelta como `{'<número>'}` |

#### Módulos de conector

Un módulo por atributo, nombrado solo por el atributo, del primer `<threadInfo>`
y del primer `<requestInfo>` del documento de estado:

| Módulo | Origen | Significado |
| --- | --- | --- |
| `maxThreads` | `threadInfo` | Hilos máximos del conector |
| `currentThreadCount` | `threadInfo` | Hilos del pool del conector |
| `currentThreadsBusy` | `threadInfo` | Hilos atendiendo una petición |
| `maxTime` | `requestInfo` | Tiempo máximo de procesamiento de una petición |
| `processingTime` | `requestInfo` | Tiempo total de procesamiento de peticiones |
| `requestCount` | `requestInfo` | Peticiones atendidas |
| `errorCount` | `requestInfo` | Peticiones terminadas en error |
| `bytesReceived` | `requestInfo` | Bytes recibidos por el conector |
| `bytesSent` | `requestInfo` | Bytes enviados por el conector |

La lista es el conjunto de atributos que un Tomcat actual publica en el
documento de estado; un atributo que el conector no publique no produce módulo.

#### Módulos de información de la JVM

El informe se filtra antes de convertirse en módulos: se descartan las líneas sin
valor, las claves que empiezan por `org.`, `java.`, `sun.`, `user.`, `package.`,
`tomcat.`, `catalina.`, `awt.` o `jdk.`, las claves que contienen `classpath`,
`librarypath`, `loader`, `path`, `separator`, `vendor.url`, `level=` o
`parent=`, y las claves que no contienen ninguno de
`vm`, `heap`, `non-heap`, `current`, `peak`, `collection`, `uptime`, `processor`,
`load`, `thread`, `compilation`, `gc` o `memory`. El nombre del módulo es la
etiqueta restante, en minúsculas y con los espacios sustituidos por guiones
bajos.

Para un Tomcat actual, los módulos que sobreviven son:

| Grupo | Módulos | Significado |
| --- | --- | --- |
| Runtime | `vmname`, `vmversion`, `vmvendor`, `uptime` | Nombre, versión y fabricante de la JVM; tiempo de actividad de la JVM en milisegundos |
| Sistema operativo | `availableprocessors`, `systemloadaverage` | Procesadores disponibles para la JVM y carga media del sistema |
| Hilos | `iscurrentthreadcputimesupported`, `isthreadcputimesupported`, `isthreadcputimeenabled`, `isthreadcontentionmonitoringsupported`, `isthreadcontentionmonitoringenabled`, `peak` | Indicadores de capacidad de la JVM y número máximo de hilos |
| Carga de clases | `totalloaded` | Clases cargadas desde el arranque de la JVM |
| Compilación | `totalcompilationtime`, `iscompilationtimemonitoringsupported` | Tiempo de compilación just-in-time y su indicador de soporte |
| Recolectores de basura | `getcollectioncount`, `getcollectiontime` | Recolecciones y tiempo de recolección, una vez por recolector con el mismo nombre |
| Heap y non-heap | `heap_init`, `heap_used`, `heap_committed`, `heap_max`, `non-heap_init`, `non-heap_used`, `non-heap_committed`, `non-heap_max` | Uso de memoria heap y non-heap, en bytes |
| Pools de memoria | `current_init`, `current_used`, `current_committed`, `current_max`, `collection_init`, `collection_used`, `collection_committed`, `collection_max`, `peak_init`, `peak_used`, `peak_committed`, `peak_max`, `getcollectionusagethreshold`, `getcollectionusagethresholdcount` | Umbrales y uso de cada pool de memoria, una vez por pool con el mismo nombre |

El conjunto exacto de módulos depende de los recolectores de basura y de los
pools de memoria de la JVM, así que otra JVM puede añadir o quitar nombres.

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.tomcat` |
| Nombre | Tomcat monitoring plugin |
| Versión | `1.0` |
| Categoría | Miscelaneus |
| Licencia | One |
| Última actualización en el Marketplace | 2026-05-25 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Ejecutable | `pandora_tomcat` |
