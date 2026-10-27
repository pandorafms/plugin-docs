# RabbitMQ monitoring plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización de RabbitMQ convierte el estado de un broker o
clúster de RabbitMQ en módulos de Pandora FMS. Cada ejecución consulta la API
HTTP de gestión de RabbitMQ y construye un conjunto de módulos: totales y tasas
de mensajes del clúster, uso de memoria y procesos por nodo, estado de cada
nodo, tasas de publicación de los exchanges, contadores de conexiones y una
comprobación de disponibilidad.

No se instala nada en los nodos de RabbitMQ. El plugin se ejecuta en el host que
usted elija y lee el broker por HTTP con un único par de credenciales.

El plugin admite dos modelos de ejecución:

- **Modo plugin de servidor** (por defecto cuando `as_agent_plugin` no aparece o
  está deshabilitado): cada ejecución construye un documento de agente y lo
  entrega a Pandora FMS mediante Tentacle o una carpeta de datos local.
- **Modo plugin de agente** (requiere `as_agent_plugin=1`): cada ejecución
  imprime los módulos generados como XML en la salida estándar, para que los
  ingiera el agente de Pandora FMS.

Esta página documenta el addon del Marketplace `pandorafms.rabbitmq`. El plugin
RabbitMQ Local que se distribuye con el agente de Pandora FMS es un addon
**distinto**: lee la misma API pero tiene sus propias claves de configuración y
genera su propio conjunto de módulos. Está documentado en
[RabbitMQ Local monitoring plugin](rabbitmq-local.md); no mezcle ambas
configuraciones.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.rabbitmq`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Un broker de RabbitMQ con el plugin de gestión habilitado | `Requerido` | El plugin lee `/api/overview`, `/api/nodes`, `/api/exchanges` y `/api/connections`, que proporciona el plugin de gestión |
| Acceso HTTP desde el host que ejecuta el plugin al puerto de escucha de gestión (TCP, `15672` por defecto en RabbitMQ) | `Requerido` | El plugin envía todas sus peticiones a la URL base de `host` |
| Un usuario de RabbitMQ autorizado a leer datos de nodos y conexiones | `Requerido` | Un único par de credenciales HTTP Basic, `user` y `pass`; la documentación de RabbitMQ indica que la etiqueta `monitoring` concede los datos de nivel de nodo y las conexiones de otros usuarios |
| `tentacle_client` en el host que ejecuta el plugin | `Requerido` cuando `transfer_mode=tentacle` | Entrega en modo plugin de servidor |
| Versiones del broker RabbitMQ | `Sin validar` | No hay una matriz de versiones registrada. La guía heredada solo indica que el plugin se desarrolló contra RabbitMQ `3.7.18`; el plugin no exige nada más allá de una API que responda a los cuatro endpoints documentados |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | No hay un sistema operativo registrado para esta versión |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores; es una declaración de catálogo que cubre este addon, no un registro de prueba del mismo |
| TLS hacia la API de gestión | `Sin validar` | El addon no tiene opción de TLS, proxy ni CA: la URL base se usa tal cual |

### Requisitos

1. **El plugin de gestión de RabbitMQ habilitado** en al menos un nodo. Viene
   incluido en la distribución de RabbitMQ y se habilita con
   `rabbitmq-plugins enable rabbitmq_management`; no hace falta reiniciar.
   Cualquier nodo con el plugin habilitado responde por todo el clúster, así que
   una sola dirección basta incluso en un despliegue de varios nodos.
2. **Acceso de red** desde el host que ejecuta el plugin a ese puerto. La
   interfaz y la API de gestión usan el puerto `15672` por defecto, y `15671`
   cuando RabbitMQ las sirve por TLS.
3. **Un usuario de RabbitMQ que pueda consultar los cuatro endpoints.** El
   plugin se autentica con HTTP Basic, así que necesita un nombre de usuario y
   una contraseña. La etiqueta `monitoring` es la que RabbitMQ documenta para
   los datos de nivel de nodo y las conexiones de otros usuarios; un usuario
   solo de monitorización se crea con esa etiqueta y con permisos de recurso
   vacíos.
4. **Pandora FMS** para recibir la salida: el servidor de Pandora FMS en modo
   plugin de servidor, o el agente de Pandora FMS del host monitorizado en modo
   plugin de agente.
5. **El cliente de Tentacle (`tentacle_client`) disponible en `PATH`**, solo
   cuando el modo plugin de servidor entrega mediante Tentacle.

La configuración de ejemplo incluida usa la cuenta `guest` de RabbitMQ. En una
instalación estándar de RabbitMQ, `guest` solo puede conectarse desde
`localhost`, así que sustitúyala por el usuario de monitorización dedicado.

### Instalar el addon

Descargue el paquete desde la entrada del Marketplace (la descarga está limitada
a usuarios con licencia):

[https://marketplace.pandorafms.com/entries/pandorafms.rabbitmq](https://marketplace.pandorafms.com/entries/pandorafms.rabbitmq)

Copie el ejecutable `rabbitmq_monitor` al host que lo vaya a ejecutar — por
ejemplo `/usr/share/pandora_server/util/plugin/rabbitmq_monitor` cuando se
ejecuta en el servidor de Pandora FMS — y coloque su archivo de configuración a
su lado o en cualquier directorio que pueda proteger. El paquete incluye además
un `rabbitmq_monitor.conf` de ejemplo; edite una copia, porque sus valores son
solo ejemplos.

No se instala nada en los nodos de RabbitMQ y no hacen falta herramientas de
cliente de RabbitMQ en el host de monitorización: todos los datos vienen de la
API HTTP de gestión.

## Configuración

El plugin combina tres fuentes, en orden creciente de precedencia:

```text
valores por defecto < archivo de configuración < argumentos de línea de comandos
```

El archivo de configuración es opcional. Cuando se usa, debe ser el **primer
argumento** de la línea de comandos; una ruta situada después de una opción no
se lee como archivo de configuración. Es un archivo de texto plano con un par
`clave=valor` por línea. Las líneas en blanco y las que empiezan por `#` se
omiten, las claves y los valores se recortan y, si una clave se repite, prevalece
la última aparición. No hay secciones: una cabecera entre corchetes se guarda
como una clave sin uso.

El nombre de archivo de los ejemplos, `rabbitmq_monitor.conf`, es una convención,
no un requisito.

### Modos de ejecución

El modo plugin de agente es la configuración más corta: el agente de Pandora FMS
ejecuta el plugin e ingiere el XML de módulos que imprime.

```ini
host=http://<TARGET_HOST>:15672
user=<USERNAME>
pass=<PASSWORD>
as_agent_plugin=1
```

El modo plugin de servidor necesita un nombre de agente y un destino de entrega.
Con Tentacle:

```ini
host=http://<TARGET_HOST>:15672
user=<USERNAME>
pass=<PASSWORD>
agent_name=RabbitMQ
interval=300
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_URL>
tentacle_port=41121
```

O copie el documento de agente en una carpeta de datos local en lugar de usar
Tentacle:

```ini
host=http://<TARGET_HOST>:15672
user=<USERNAME>
pass=<PASSWORD>
agent_name=RabbitMQ
interval=300
transfer_mode=local
local_folder=/var/spool/pandora/data_in
```

La misma ejecución en modo plugin de agente solo con argumentos, sin archivo de
configuración:

```bash
./rabbitmq_monitor -host http://<TARGET_HOST>:15672 -user <USERNAME> -pass <PASSWORD> -as_agent_plugin 1
```

Puntos clave:

- **`host` es la URL base de la API de gestión**, con el esquema y el puerto:
  `http://<TARGET_HOST>:15672`. El plugin añade las rutas `/api/...` a este
  valor, así que un `host:puerto` sin esquema no es una URL de petición
  completa. El ejemplo incluido (`host=192.168.80.20:8080`) es un valor de
  relleno con un puerto que no es el habitual; sustitúyalo.
- **`user` y `pass` se envían como credenciales HTTP Basic en cada petición.**
  Deben pertenecer a un usuario que pueda leer los endpoints enumerados en
  [Requisitos](#requisitos). No hay token, certificado ni otra superficie de
  autenticación.
- **`as_agent_plugin` selecciona el modelo.** `1` (o cualquier valor numérico
  mayor que `0`) imprime el XML de módulos en la salida estándar; `0`, un valor
  vacío o un valor no numérico mantiene el modo plugin de servidor.
  `as_server_plugin=0` también selecciona el modo plugin de agente cuando
  `as_agent_plugin` no aparece, y `as_agent_plugin` prevalece cuando ambas claves
  están presentes.
- **`agent_name` da nombre al agente creado en Pandora FMS** e `interval` es su
  intervalo en segundos. Ambos son exclusivos del modo plugin de servidor.
- **`transfer_mode` selecciona la entrega.** `tentacle` (distingue mayúsculas y
  minúsculas) ejecuta el cliente de Tentacle; cualquier otro valor copia el
  documento de agente en `local_folder`.
- **`module_group` da nombre al grupo de módulos asignado a todos los módulos
  generados.** `module_interval` y `module_tag_list` fijan de la misma forma el
  intervalo y las etiquetas de los módulos. Cuando no aparecen, los módulos no
  llevan grupo, ni intervalo propio, ni etiquetas.
- **Un agente por broker.** Los nombres de módulo no llevan prefijo del broker,
  así que dos brokers entregados al mismo agente se sobrescriben los módulos
  entre sí. Use un `agent_name` distinto por broker, o una instalación de plugin
  de agente por broker.

En modo plugin de agente, el ejecutable se declara como plugin del agente de
Pandora FMS — en el archivo de configuración del agente o mediante configuración
remota — con el archivo de configuración como primer argumento del comando del
plugin y `as_agent_plugin=1` dentro de ese archivo. El agente ejecuta el plugin,
lee el XML de módulos de la salida estándar y publica los módulos en su propio
agente, así que `agent_name`, `interval` y las claves de transferencia no se usan
en este modo.

### Credenciales y transporte

- El plugin no tiene opciones de TLS propias: solicita la URL base que usted le
  dé. Con una URL base `http://`, las credenciales y las métricas recogidas
  viajan sin cifrar, así que mantenga el puerto de gestión en una red de
  confianza o publíquelo a través de un terminador TLS. RabbitMQ sirve la API de
  gestión por HTTPS en el puerto `15671` cuando está configurado con TLS; una URL
  base `https://` depende del soporte TLS disponible en el ejecutable y aquí no
  está validada.
- No existe clave de CA, de proxy ni de verificación de certificado. Un
  certificado privado o autofirmado no tiene, por tanto, una ruta de
  configuración soportada en este addon.
- `pass` se guarda en el archivo de configuración en texto plano: restrinja los
  permisos del archivo al usuario que ejecuta el plugin (por ejemplo
  `chmod 600`).
- Evite `-pass` en la línea de comandos: el comando queda en el historial del
  shell y la lista de procesos del sistema operativo puede exponerlo mientras el
  plugin se ejecuta. Un plugin de servidor programado conserva sus parámetros en
  la base de datos de Pandora FMS, así que trate también la definición del
  módulo como sensible.

### Registrar el plugin en Pandora FMS

`rabbitmq_monitor` también se puede registrar en la consola de Pandora FMS como
plugin de servidor estándar, de forma que Pandora FMS lo ejecute en el servidor
que ejecuta los módulos en lugar de en una línea de comandos. Registrado así, el
plugin mantiene el modo plugin de servidor: cada ejecución construye el
documento de agente y lo entrega, y el agente con sus módulos aparece en la
consola.

1. Abra **Servers → Plugins** y haga clic en **Register Plugin**.
2. Indique el nombre, el tipo de plugin **Standard**, un tiempo de espera
   máximo opcional y una descripción.
3. En **Plugin command**, escriba la ruta absoluta a `rabbitmq_monitor` en el
   servidor de Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/rabbitmq_monitor`.
4. En **Plugin parameters**, pase las claves documentadas y use las macros
   `_field1_`, `_field2_`, ... como marcadores de posición. Para un broker en
   modo plugin de servidor con Tentacle:

    ```text
    -host _field1_ -user _field2_ -pass _field3_ -agent_name _field4_ -transfer_mode tentacle -tentacle_ip 127.0.0.1 -tentacle_port 41121
    ```

5. En **Macro parameters**, describa cada campo. El ejemplo usa estos valores:

    | Campo | Descripción | Valor de ejemplo |
    | --- | --- | --- |
    | `_field1_` | URL base de la API de gestión, con esquema y puerto | `http://<TARGET_HOST>:15672` |
    | `_field2_` | Usuario de RabbitMQ autorizado a leer la API de gestión | `<USERNAME>` |
    | `_field3_` | Contraseña de ese usuario; marque **Hide value** | — |
    | `_field4_` | Nombre del agente que alojará los módulos | `RabbitMQ` |

`-tentacle_ip 127.0.0.1` entrega al servidor de Tentacle de la máquina que
ejecuta el plugin, así que el agente llega al servidor de Pandora FMS que ejecuta
el módulo. Para copiar el documento en una carpeta de datos local, sustituya los
parámetros de Tentacle por
`-transfer_mode local -local_folder /var/spool/pandora/data_in`.

<!-- SCREENSHOT NEEDED: Formulario de registro de plugins de servidor en la consola de Pandora FMS, con el comando del plugin rabbitmq_monitor y sus campos de parámetros y macros. -->

Una vez registrado, el plugin está disponible al crear módulos de plugin y cada
módulo rellena los campos individualmente. El módulo se ejecuta en el servidor
seleccionado para él, incluido un servidor de Pandora FMS remoto, de modo que
cada broker se monitoriza desde el servidor de Pandora FMS más cercano sin
instalar nada en el host del broker.

## Verificación

Ejecute el plugin manualmente desde una terminal, pasando el archivo de
configuración como primer argumento:

```bash
./rabbitmq_monitor /etc/pandora/plugins/rabbitmq_monitor.conf
```

La forma relativa `./rabbitmq_monitor rabbitmq_monitor.conf` funciona cuando la
terminal ya está en el directorio que contiene ambos archivos. Cada ejecución se
realiza una vez y termina.

Una línea de comandos vacía imprime el resumen de uso:

```text
- Syntax:

./rabbitmq_monitor <plugin_configuration_file_path>
```

No hay opción de ayuda: `-h` y `--help` se tratan como cualquier otro argumento.

En modo plugin de agente, una ejecución correcta imprime en la salida estándar un
bloque XML `<module>` por cada módulo generado. Este es un extracto del documento
que se construye para un clúster de un solo nodo:

```xml
<module>
	<name><![CDATA[Cluster name]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[rabbit@node01]]></data>
</module>
<module>
	<name><![CDATA[Availability]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Rabbit MQ API availability]]></description>
</module>
<module>
	<name><![CDATA[Memory used - rabbit@node01]]></name>
	<type>generic_data</type>
	<data><![CDATA[174895104]]></data>
	<description><![CDATA[Usually in bytes. Represents the total memory that the RabbitMQ node is using at that instant.]]></description>
</module>
```

`Availability` vale `1` solo cuando la petición de resumen tiene éxito; un `0`
en ese módulo significa que la petición de resumen no devolvió HTTP 200 (consulte
[Operación y resolución de problemas](#operacion-y-resolucion-de-problemas)).

En modo plugin de servidor, una ejecución imprime `1` y termina. Ese `1` se
imprime después del intento de entrega, **no** como su resultado: una entrega por
Tentacle fallida o una copia local fallida también imprimen `1`. Confirme el
agente y sus módulos en la consola.

<!-- SCREENSHOT NEEDED: Vista del agente en la consola de Pandora FMS con los módulos generados por el plugin rabbitmq_monitor para un broker. -->

## Entender los resultados

El catálogo de módulos es fijo. Cada ejecución emite ocho módulos, añade seis
cuando la petición de resumen tiene éxito y añade cinco por nodo cuando la
petición de nodos tiene éxito. Un clúster de un solo nodo con la API en buen
estado produce por tanto 19 módulos.

- **Disponibilidad y contadores de conexiones (siempre).** `Availability`,
  `Total connections`, `Connections running`, `Connections blocked`,
  `Total received octets`, `Total sent octets`, `Exchanges in rate` y
  `Exchanges out rate` se generan en cada ejecución, aunque no tenga éxito
  ninguna petición.
- **Totales del clúster (petición de resumen).** `Cluster name`,
  `Total queue messages`, `Messages unacknowledged`, `Total exchanges`,
  `Queue publish rate`, `Queue deliver get rate` y `Queue deliver noack rate` se
  generan solo cuando `/api/overview` responde con HTTP 200.
- **Por nodo (petición de nodos).** Por cada nodo que devuelve la API se generan
  `Memory used - <node>`, `Memory rate`, `Proc used - <node>`, `Proc details` y
  `Node status - <node>`. Si la petición de nodos falla, no se genera ninguno de
  estos módulos y el resto de la ejecución no se ve afectado.

Cómo se leen los valores:

- **Las tasas son tasas por segundo** tomadas de los campos `rate` que calcula la
  API de gestión con su propio intervalo de muestreo. `Memory rate` y
  `Proc details` son las tasas de memoria y de procesos de un nodo;
  `Exchanges in rate` y `Exchanges out rate` son tasas de publicación de **un**
  exchange, no totales del clúster: el plugin recorre la lista de exchanges y se
  queda con el último que informa de una tasa distinta de cero. Cuando ninguno la
  informa, ambos módulos valen `0`.
- **`Connections blocked` es toda conexión cuyo estado no sea exactamente
  `running`.** No es un recuento de conexiones en el estado `blocked` de
  RabbitMQ.
- **`Total received octets` y `Total sent octets`** son la suma de las tasas de
  octetos recibidos y enviados de cada conexión, así que son caudal en octetos
  por segundo, no totales acumulados.
- **`Memory rate` y `Proc details` no llevan el nombre del nodo**, a diferencia
  de los otros tres módulos por nodo. En un clúster con más de un nodo, cada nodo
  añade su propio módulo con el mismo nombre, de modo que estas dos series no se
  pueden atribuir a un nodo. Úselas solo en clústeres de un solo nodo, donde el
  nombre no es ambiguo.
- **`Queue deliver get rate` no informa de lo que dice su nombre.** El módulo lee
  la tasa de publicación cuando la tasa de obtención está presente, así que en la
  práctica repite `Queue publish rate` o vale `0`. Use `Queue publish rate` para
  la actividad de publicación y no configure alertas sobre
  `Queue deliver get rate`.

Cuando no se puede alcanzar la API de gestión — credenciales incorrectas,
problema de red, plugin de gestión deshabilitado — fallan todas las peticiones:
`Availability` vale `0`, los seis módulos de clúster y los cinco módulos por nodo
no se generan, y los siete módulos restantes valen `0`.

El documento de agente creado en modo plugin de servidor lleva el nombre y el
alias de `agent_name` y el intervalo de `interval`. Su atributo de dirección se
deriva de `host` separando por `:`; en esta versión contiene el número de partes
separadas por dos puntos (por ejemplo `3` para `http://<TARGET_HOST>:15672`), no
la dirección del broker, así que no espere que el campo de dirección del
agente muestre el broker.

## Operación y resolución de problemas

### Operación diaria

- El plugin no guarda estado entre ejecuciones: cada ejecución lee el broker en
  ese momento, así que se puede lanzar manualmente en cualquier instante.
- En modo plugin de servidor, prográmelo desde Pandora FMS (el planificador de
  plugins de servidor o `cron`) o desde cualquier planificador externo. En modo
  plugin de agente, el agente de Pandora FMS lo ejecuta según la planificación de
  plugins configurada. `interval` solo fija el intervalo del agente creado en la
  consola; no planifica el plugin.
- **Use `debug=1` para el diagnóstico.** El addon escribe sus propios mensajes en
  la salida de error solo cuando `debug` está habilitado: los errores de escritura
  del archivo temporal, la salida de Tentacle y los errores de copia local son
  silenciosos sin él. `debug` no escribe en la salida estándar, así que no
  corrompe el XML de módulos en modo plugin de agente.
- El documento de agente se escribe en la carpeta de `tmp` (`/tmp` por defecto)
  como `<agent_name>.<epoch>.data`, y el archivo se elimina tras una entrega
  correcta por Tentacle o local. Una entrega fallida lo deja en su sitio: revise
  esa carpeta cuando las entregas fallen de forma repetida y vacíela una vez
  corregida la causa.
- Una ejecución detenida con `SIGTERM` imprime `Received SIGTERM, exiting...` y
  termina con estado `0`, así que un tiempo de espera agotado parece una
  ejecución correcta. Configure un tiempo máximo en la definición del plugin solo
  si puede verificar el tiempo de ejecución esperado para el tamaño de su broker.
- Cree un agente por broker, con un `agent_name` distinto, y use `module_group`
  para separar estos módulos del resto en el mismo agente.

### Resolución de problemas

- **`Availability` vale `0`** — la petición de resumen no devolvió HTTP 200.
  Compruebe que el plugin de gestión está habilitado, que `host` apunta al
  puerto de gestión de un nodo que responde por el clúster y que usuario y
  contraseña se autentican. Un `401`/`403` de RabbitMQ, un host inalcanzable, un
  puerto incorrecto y un plugin deshabilitado producen el mismo resultado: el
  plugin solo lee respuestas HTTP 200 y no informa de error para las demás.
- **No aparecen módulos por nodo** mientras `Availability` vale `1` — la petición
  de nodos falló. Los usuarios con la etiqueta `monitoring` ven los datos de
  nivel de nodo; un usuario sin esa etiqueta es rechazado. El resto de la
  ejecución sigue generando sus módulos.
- **Todos los valores son `0`** — la petición de resumen falló mientras las
  peticiones posteriores devolvieron listas vacías: es la misma causa que un
  `Availability` de `0`.
- **El agente nunca aparece en la consola en modo plugin de servidor** — la
  entrega falló y la ejecución imprimió `1` de todos modos. Vuelva a ejecutar una
  vez con `debug=1` para ver el motivo y compruebe después que `tentacle_client`
  está instalado y en `PATH`, que `tentacle_ip:tentacle_port` es alcanzable, o
  que `local_folder` existe y es escribible por el usuario que ejecuta el plugin.
- **Líneas `ERROR: ...`** — el plugin imprime sus propios errores de
  configuración en la salida estándar, antes del resumen de uso, y aun así
  termina con estado `0`. Lea la salida, no el estado de salida.
- **No se informa de un valor obligatorio** — las comprobaciones de valores
  obligatorios solo se ejecutan cuando quedan al menos dos argumentos después de
  consumir el archivo de configuración. Con la forma documentada de un solo
  archivo (`./rabbitmq_monitor rabbitmq_monitor.conf`) no se ejecutan: la falta
  de `host`, `user`, `pass`, `agent_name`, `tentacle_ip` o `local_folder` no se
  informa y la ejecución continúa con los valores que tenga. Ejecute siempre una
  vez con una opción explícita (`debug=1` sirve) después de editar el archivo,
  o verifique el primer resultado en la consola.
- **Los módulos no se actualizan y el broker está sano** — revise la
  planificación de ejecución del plugin en Pandora FMS y el intervalo del agente,
  y ejecute el plugin manualmente con `debug=1` para confirmar que la API de
  gestión responde desde el host que lo ejecuta.
- **Una URL base `https://` con un certificado privado** — el addon no tiene
  opción de CA ni de verificación, así que un certificado privado o autofirmado
  no tiene una ruta soportada aquí. Monitorice el puerto HTTP simple desde una
  red de confianza, o termine TLS delante de RabbitMQ con un certificado en el
  que confíe el host.

## Referencia

### Claves del archivo de configuración

| Nombre | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `host` | Sí | — | URL base de la API de gestión de RabbitMQ, con esquema y puerto, por ejemplo `http://<TARGET_HOST>:15672`. El plugin añade a este valor `/api/overview`, `/api/nodes`, `/api/exchanges` y `/api/connections`. |
| `user` | Sí | — | Usuario de RabbitMQ enviado como credenciales HTTP Basic. |
| `pass` | Sí | — | Contraseña de `user`. |
| `agent_name` | Obligatoria en modo plugin de servidor | — | Nombre y alias del agente creado en Pandora FMS. |
| `interval` | No | `300` | Solo en modo plugin de servidor. Intervalo del agente creado, en segundos. |
| `as_agent_plugin` | No | `0` (modo plugin de servidor) | `1` (o cualquier valor numérico mayor que `0`) imprime el XML de módulos en la salida estándar. `0`, vacío o no numérico mantiene el modo plugin de servidor. |
| `as_server_plugin` | No | `1` | El lector de configuración la acepta. `0` selecciona el modo plugin de agente cuando `as_agent_plugin` no aparece; `as_agent_plugin` prevalece cuando ambas están presentes. |
| `transfer_mode` | Obligatoria en modo plugin de servidor | Vacío | `tentacle` entrega con el cliente de Tentacle; cualquier otro valor copia el documento en `local_folder`. |
| `local_folder` | Obligatoria cuando `transfer_mode` no es `tentacle` | — | Carpeta de destino de la copia del documento de agente. |
| `tentacle_ip` | Obligatoria cuando `transfer_mode=tentacle` | — | Dirección del servidor de Tentacle. |
| `tentacle_port` | No | `41121` | Puerto del servidor de Tentacle. |
| `tentacle_client` | No | `tentacle_client` | Ejecutable del cliente de Tentacle, resuelto en `PATH` o indicado con ruta absoluta. |
| `tentacle_opts` | No | Vacío | Opciones adicionales pasadas al cliente de Tentacle, separadas por espacios. |
| `tmp` | No | `/tmp` | Carpeta donde se escribe el documento de agente antes de la entrega. |
| `module_group` | No | Vacío (sin grupo) | Grupo de módulos asignado a todos los módulos generados. |
| `module_interval` | No | Vacío (intervalo del agente) | Intervalo de módulo asignado a todos los módulos generados. |
| `module_tag_list` | No | Vacío (sin etiquetas) | Etiquetas de módulo asignadas a todos los módulos generados, tal cual se indican. |
| `debug` | No | `0` | `1` (o cualquier valor numérico mayor que `0`) escribe mensajes de diagnóstico, la salida de Tentacle y los errores de entrega en la salida de error. |

Las claves booleanas se habilitan con cualquier valor numérico mayor que `0`;
`0`, un valor vacío o un valor no numérico significa deshabilitado. Las claves
desconocidas se aceptan y se ignoran: el plugin no valida el conjunto de claves.

### Ejecución por línea de comandos

```bash
./rabbitmq_monitor [config-file] [ -key value ... ]
```

| Condición | Comportamiento |
| --- | --- |
| La línea de comandos está vacía | El plugin imprime el resumen de uso y termina con estado `0` |
| El primer argumento nombra un archivo existente | Se lee como archivo de configuración y se retira de la lista de argumentos |
| El primer argumento no es un archivo existente | No se lee como configuración; la ejecución continúa con los valores por defecto más las opciones |
| `-key value` | Sustituye el valor de `key` |
| `--key value` o `-key=value` | No se reconocen: solo se elimina un guion inicial, así que el par se guarda bajo una clave que el plugin ignora y la clave documentada conserva su valor de archivo o por defecto |
| Argumentos que no forman un par `-key value` | Se ignoran; un argumento final sin valor no se informa |
| `-h` o `--help` | No son una opción de ayuda; la opción se ignora y la ejecución continúa |
| Error de configuración | Se informa en la salida estándar, seguido del resumen de uso, con estado `0` |

Las opciones pueden ir antes o después de la ruta del archivo de configuración,
pero solo un archivo en la primera posición se lee como archivo de
configuración.

### Comportamiento de la entrega

| Situación | Resultado |
| --- | --- |
| `transfer_mode=tentacle` y la entrega tiene éxito | El archivo temporal se elimina después de la entrega |
| `transfer_mode=tentacle` y la entrega falla | No se entrega nada; el mensaje del cliente se escribe en la salida de error solo con `debug=1`, y el archivo temporal queda en `tmp` |
| Cualquier otro `transfer_mode` | El documento se copia en `local_folder` y el archivo temporal se elimina; un error de copia se escribe en la salida de error solo con `debug=1` |
| `transfer_mode` vacío | No se entrega nada; el motivo se escribe en la salida de error solo con `debug=1` |
| Resultado de la entrega en la salida estándar | Se imprime un `1` en todos los casos |
| Estado de salida | `0` tanto para errores de configuración como para entregas fallidas y `SIGTERM` |

### Módulos generados

`<node>` es un nombre de nodo informado por el broker. Los nombres de módulo se
crean exactamente como se indican, sin prefijo del broker ni de la instancia.

| Nombre del módulo | Tipo | Significado | Se genera cuando |
| --- | --- | --- | --- |
| `Cluster name` | `generic_data_string` | Nombre del clúster informado por el broker | La petición de resumen tiene éxito |
| `Total queue messages` | `generic_data` | Total de mensajes en todas las colas | La petición de resumen tiene éxito |
| `Messages unacknowledged` | `generic_data` | Mensajes entregados pero no confirmados | La petición de resumen tiene éxito |
| `Total exchanges` | `generic_data` | Número de exchanges | La petición de resumen tiene éxito |
| `Queue publish rate` | `generic_data` | Tasa de publicación del clúster | La petición de resumen tiene éxito |
| `Queue deliver get rate` | `generic_data` | Informa de la tasa de publicación cuando hay una tasa de obtención (véase [Entender los resultados](#entender-los-resultados)) | La petición de resumen tiene éxito |
| `Queue deliver noack rate` | `generic_data` | Mensajes entregados a consumidores sin confirmación | La petición de resumen tiene éxito |
| `Availability` | `generic_proc` | `1` cuando la petición de resumen devuelve HTTP 200, `0` en caso contrario | Siempre |
| `Memory used - <node>` | `generic_data` | Memoria usada por el nodo, en bytes | La petición de nodos tiene éxito |
| `Memory rate` | `generic_data` | Tasa a la que el nodo consume o libera memoria | La petición de nodos tiene éxito |
| `Proc used - <node>` | `generic_data` | Procesos Erlang usados por el nodo | La petición de nodos tiene éxito |
| `Proc details` | `generic_data` | Tasa a la que se crean o terminan los procesos Erlang del nodo | La petición de nodos tiene éxito |
| `Node status - <node>` | `generic_proc` | `1` mientras el nodo está en ejecución, `0` en caso contrario | La petición de nodos tiene éxito |
| `Exchanges in rate` | `generic_data` | Tasa de publicación entrante del último exchange que informa de una; `0` cuando ninguno registra actividad | Siempre |
| `Exchanges out rate` | `generic_data` | Tasa de publicación saliente del último exchange que informa de una; `0` cuando ninguno registra actividad | Siempre |
| `Total connections` | `generic_data` | Número de conexiones devueltas por la API | Siempre |
| `Connections running` | `generic_data` | Conexiones cuyo estado es exactamente `running` | Siempre |
| `Connections blocked` | `generic_data` | Conexiones cuyo estado no es `running` | Siempre |
| `Total received octets` | `generic_data` | Suma de las tasas de octetos recibidos de todas las conexiones | Siempre |
| `Total sent octets` | `generic_data` | Suma de las tasas de octetos enviados de todas las conexiones | Siempre |

Los módulos no llevan umbrales, unidades ni plantillas de alerta: configúrelos en
la consola.

### Identidad del addon

| Campo | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.rabbitmq` |
| Nombre en el Marketplace | RabbitMQ monitoring plugin |
| Versión del addon | `1.1` |
| Última actualización en el Marketplace | 2025-08-26 |
| Paquete del Marketplace | `pandorafms.rabbitmq.1.1.zip` |
| Licencia | `One` (descarga limitada a usuarios con licencia) |
| Tipo en el Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de monitorización, modo plugin de agente o de servidor |
| Ejecutable | `rabbitmq_monitor` |
