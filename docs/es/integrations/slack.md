# Integración con Slack

*Última actualización del artículo: 2026-10-27.*

## Qué hace

La integración con Slack entrega las alertas de Pandora FMS a un canal de Slack como mensajes de
chat. Cuando una alerta se dispara o se recupera, Pandora FMS ejecuta un conector en el servidor que
procesa la alerta y el conector publica los campos de la alerta a través de la API web de Slack, con
la identidad de la aplicación de Slack que usted autoriza.

El conector viene con Pandora FMS. No tiene entrada en el Marketplace ni hay nada que descargar del
catálogo: el ejecutable y el comando de alerta predeterminado llamado **Pandora Slack** ya forman
parte del producto, y usted solo añade el lado de Slack y las credenciales.

Cada ejecución publica **dos mensajes** de forma predeterminada: la alerta (un emoji, un título en
negrita, una descripción en cursiva y una línea `clave : valor` por cada par de datos) y, por
separado, un mensaje de pie con el texto `PandoraFMS`. Ambos son configurables y el pie se puede
suprimir.

De forma opcional, el conector puede adjuntar la imagen del gráfico de un módulo obtenida de la API de
Pandora FMS. Esa ruta depende de un método de carga de ficheros de Slack que Slack retiró, así que la
imagen ya no se entrega. El texto de la alerta no se ve afectado. Consulte
[Entender la integración](#entender-la-integracion).

## Preparar el servicio externo

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Un espacio de trabajo de Slack donde pueda crear e instalar una aplicación | `Required` | El conector se autentica con el token de bot de una aplicación de Slack, por lo que la aplicación debe existir y estar instalada en el espacio de trabajo |
| Una aplicación de Slack con usuario de bot y el permiso `chat:write` | `Required` | Todos los mensajes se publican con `chat.postMessage`, que requiere `chat:write` |
| La aplicación como miembro del canal de destino, o el permiso `chat:write.public` | `Required` | Slack rechaza la publicación de una aplicación que no está en el canal con `not_in_channel`; `chat:write.public` permite canales públicos sin unirse |
| Salida HTTPS desde el servidor de Pandora FMS hacia `slack.com` (TCP `443`) | `Required` | Todas las llamadas van a la API web de Slack |
| Versión de Pandora FMS que incluye el comando **Pandora Slack** | `Not validated` | No existe un registro de validación por versión para este conector |
| Sistema operativo del servidor de Pandora FMS | `Not validated` | No se ha registrado ningún sistema operativo para este conector |
| Un proxy corporativo o interceptación TLS entre el servidor y Slack | `Not validated` | El conector no tiene opción propia de proxy ni de CA; consulte [Resolución de problemas](#resolucion-de-problemas) |

### Crear la aplicación de Slack

1. Abra `https://api.slack.com/apps` y elija **Create New App** → **From scratch**.
2. Escriba un nombre, seleccione el espacio de trabajo propietario del canal y confirme.
3. Abra **OAuth & Permissions**, vaya a **Scopes** → **Bot Token Scopes** y añada `chat:write`.
4. Elija **Install to Workspace** y autorice la aplicación.
5. Copie el **Bot User OAuth Token**. Empieza por `xoxb-`; es el valor que necesita el conector.

<!-- SCREENSHOT NEEDED: página "OAuth & Permissions" de la aplicación de Slack con la sección Bot Token Scopes mostrando chat:write y el nombre de la aplicación anonimizado. -->

<p class="callout warning">El conector se autentica con un token de bot. Una URL de <strong>Incoming Webhook</strong> no funciona: el conector publica a través de la API web de Slack, así que una URL de webhook copiada en el parámetro del token se rechaza con un error de autenticación. Ignore las instrucciones que le pidan activar Incoming Webhooks para esta integración.</p>

### Invitar la aplicación al canal

En el canal de destino ejecute `/invite @<APP_NAME>` y seleccione la aplicación que creó. Slack exige
que la aplicación sea miembro de la conversación: una publicación en un canal al que la aplicación no
se ha unido falla con `not_in_channel`. Como alternativa, solicite el permiso `chat:write.public` y
reinstale la aplicación; ese permiso cubre los canales públicos a los que la aplicación no se ha
unido, pero no los canales privados.

### Obtener el identificador del canal

Abra el canal de destino, abra sus detalles y copie el identificador del canal. Empieza por `C` en un
canal público y por `G` en uno privado. El nombre del canal también funciona, pero el identificador es
el único valor que sobrevive a un cambio de nombre, así que es preferible.

## Configurar Pandora FMS

### Colocar el conector en el servidor

1. Asegúrese de que el conector está en el servidor de Pandora FMS, en un directorio legible y
   ejecutable por el usuario que ejecuta el servidor de Pandora FMS; cópielo desde su paquete si no
   está. El comando predeterminado usa `/usr/share/pandora_server/util/plugin/`.
2. Instale los requisitos de ejecución que incluye el paquete antes de la primera ejecución. El
   paquete incluye un fichero de requisitos para ellos.
3. Haga que la ruta instalada coincida con el comando de alerta. El comando incluido llama a
   `/usr/share/pandora_server/util/plugin/pandora-slack-cli`, sin extensión, mientras que el fichero
   empaquetado se llama `pandora-slack-cli.py`. Renombre el fichero a `pandora-slack-cli` o edite el
   comando para que nombre el fichero que instaló.
4. Repita la copia en cada servidor de Pandora FMS que pueda procesar alertas. El comando no es
   interno de la consola, así que lo ejecuta el servidor que dispara la alerta.

### Editar el comando de alerta incluido

La consola ya contiene el comando de alerta **Pandora Slack**. Abra **Alerts** → **Commands** y edítelo;
si su instalación no tiene ese comando, cree uno con la misma línea de comandos. En ambos casos:

1. Sustituya el `TOKEN` literal de la línea de comandos por el token de bot que copió.
2. Deje el resto de la línea de comandos como está, o ajuste la ruta de instalación (paso anterior).

La línea de comandos incluida es:

```text
/usr/share/pandora_server/util/plugin/pandora-slack-cli -t "TOKEN" -d "_field1_" -c "_field2_" -e "_field3_" -T "_field4_" -D "_field5_"
```

Los cinco campos usan estas descripciones y valores predefinidos en la consola:

| Campo | Descripción en la consola | Valor predefinido | Función |
| --- | --- | --- | --- |
| 1 | `Data in coma separate keypairs` | `data=_data_` | Un par `clave=valor` por cada dato del mensaje |
| 2 | `Slack channel id/name` | vacío | Canal que recibe la alerta |
| 3 | `Title emoji` | `:red_circle:,Red circle;:green_circle:,Green circle` | Emoji que precede a la línea del título; el valor predefinido es una lista de dos entradas |
| 4 | `Title` | `[PANDORA] Alert FIRED on _agent_ / _module_` | Línea del título, en negrita |
| 5 | `Description` | `_agent_ \| _module_ \| _data_ \| _timestamp_` | Línea en cursiva bajo el título |

El token está escrito en el **cuerpo del comando**, no en un campo. Esto difiere de las instrucciones
antiguas que lo colocan en el segundo campo: en el comando incluido, el campo 2 es el canal y el token
es el `TOKEN` literal que usted sustituye. Si prefiere mantener el token fuera del cuerpo del comando,
sustituya `-t "TOKEN"` por la referencia a un campo libre, describa ese campo y marque su casilla
**Hide**. Ocultar un campo solo lo enmascara en la consola; el valor se sigue sustituyendo en la línea
de comandos cuando se ejecuta la alerta.

<!-- SCREENSHOT NEEDED: formulario de edición del comando de alerta "Pandora Slack" con la línea de comandos y el token tapado, y las cinco filas de campos con sus descripciones y valores predefinidos. -->

### Crear o editar la acción de alerta

Abra **Alerts** → **Actions** y edite la acción **Pandora Slack**, que viene como acción
predeterminada. Sus campos vienen rellenos a partir del comando; compruebe tres cosas:

- El campo 2 (canal) está **vacío**: introduzca el identificador del canal.
- Los campos de **Triggering** usan `:red_circle:` y los de **Recovery** usan `:green_circle:`.
- Triggering y Recovery tienen su propio título y su propia descripción, que puede reescribir.
  Conserve las macros: transportan el agente, el módulo, el valor y la marca de tiempo a Slack.

<!-- SCREENSHOT NEEDED: formulario de la acción de alerta "Pandora Slack" con un identificador de canal de laboratorio, las filas de campos de disparo y recuperación, y sin canales ni credenciales reales. -->

### Asociar la acción a lo que monitoriza

Cree o edite una plantilla de alerta en **Alerts** → **Templates**, añada esta acción a la plantilla y
aplique la plantilla a los módulos o a la política que debe notificar a Slack. Consulte el manual de
Pandora FMS sobre
[alertas](https://pandorafms.com/manual/es/documentation/pandorafms/management_and_operation/01_alerts)
para plantillas, acciones y sustitución de macros.

## Verificar

Ejecute el conector una vez a mano en el servidor de Pandora FMS antes de confiar en una alerta:

```bash
/usr/share/pandora_server/util/plugin/pandora-slack-cli \
  -t "<API_TOKEN>" \
  -c "<CHANNEL_ID>" \
  -d "Agent=<AGENT_NAME>,Module=<MODULE_NAME>,Status=Critical,Data=22" \
  -T "Pandora FMS test alert" \
  -D "Manual verification" \
  -F ""
```

Una ejecución correcta imprime exactamente una línea en la salida estándar:

```text
> Message sent successfully
```

y el canal recibe un mensaje:

```text
:red_circle: *Pandora FMS test alert*
_Manual verification_

*Agent* : <AGENT_NAME>
*Module* : <MODULE_NAME>
*Status* : Critical
*Data* : 22
```

Como el ejemplo pasa `-F ""`, no se publica ningún mensaje de pie. Quite ese argumento y la misma
ejecución publicará un segundo mensaje que contiene solo `PandoraFMS`.

Dos comprobaciones completan la verificación:

1. **El conector por sí solo** — la ejecución manual anterior. Si falla aquí, la consola no puede
   tener éxito.
2. **La ruta de la consola** — dispare la alerta desde un módulo con la acción asociada y confirme que
   el mensaje llega al canal con el agente, el módulo y el valor de esa alerta.

No use el código de salida para decidir si la entrega funcionó: el conector también termina con estado
`0` después de un error de Slack (consulte [Códigos de salida](#codigos-de-salida)). Mire el canal y el
mensaje que imprimió el conector.

## Entender la integración

### Flujo

1. Una alerta se dispara o se recupera y Pandora FMS selecciona las acciones de la plantilla de
   alerta.
2. El servidor sustituye las macros de la alerta en los campos del comando (`_agent_`, `_module_`,
   `_data_`, `_timestamp_`, `_field1_`…`_field5_`) y ejecuta la línea de comandos del comando de
   alerta.
3. El conector convierte `-d` en las líneas de datos, las une con el título, la descripción y el
   emoji, y llama a `chat.postMessage` con ese texto.
4. Si hay un pie configurado, llama a `chat.postMessage` una segunda vez solo con el texto del pie.
5. Si se pidió el gráfico de un módulo, obtiene la imagen de la API de Pandora FMS e intenta subirla al
   canal.

El conector no guarda estado y no tiene cola: cada ejecución es una llamada HTTP síncrona desde el
servidor que procesa la alerta. Una llamada fallida se informa en la salida del comando y no se
reintenta.

### Composición del mensaje

- La primera línea es el emoji seguido del título en negrita: `:red_circle: *<TITLE>*`.
- La segunda línea es la descripción en cursiva. Una descripción vacía deja una línea en cursiva
  vacía, no la omite.
- Después, una línea en blanco y una línea por cada par de datos, con la clave en negrita:
  `*<KEY>* : <VALUE>`.
- Los pares se leen de izquierda a derecha, con `=` como separador entre clave y valor y `,` entre
  pares. Un valor que contiene `=` rompe el par: se imprime el aviso
  `Warning, error parsing keypairs values: too many values to unpack` y los pares posteriores se
  descartan.
- Slack aplica su propio formato y puede reescribir parte del texto (los enlaces, por ejemplo). El
  conector compara el texto que devuelve Slack con el que envió, así que un mensaje reescrito produce
  una traza de error **después** de haberse entregado el mensaje (consulte
  [Resolución de problemas](#resolucion-de-problemas)).

### Limitaciones de entrega

- Slack acepta aproximadamente un mensaje por segundo y canal de una aplicación. Con el pie
  predeterminado, cada alerta consume dos de esas posiciones, y una ráfaga de alertas a un mismo canal
  puede recibir limitación de frecuencia.
- El mensaje es texto plano con el marcado de Slack. El conector no envía bloques, adjuntos ni
  elementos interactivos.
- No hay reintentos ni persistencia: si el servidor no puede alcanzar Slack en ese momento, esa alerta
  no se entrega.

### Los gráficos de módulo ya no se entregan

La ruta del gráfico existe y se documenta por completitud, pero hoy no puede tener éxito:

- El conector pide el gráfico a la API externa de Pandora FMS (`module_graph`), lo decodifica y lo
  escribe en `--tmp_dir` como `graph_<module_id>.<epoch>.png`.
- Después sube el fichero con el método `files.upload` de Slack. Slack declaró obsoleto ese método y lo
  detuvo el **12 de noviembre de 2025**, así que la carga se rechaza y el conector imprime
  `File Got an error: <error>`. En ese momento el texto de la alerta ya se ha enviado.
- El fichero temporal se elimina al final de la ejecución. Dos ejecuciones del mismo módulo en el
  mismo segundo comparten el mismo nombre de fichero.

Tenga en cuenta además que `--api_conf` lleva la contraseña y la clave de API de Pandora FMS en la
línea de comandos, así que son visibles en la lista de procesos mientras se ejecuta la alerta.

### TLS y proxies

- Al arrancar, el conector impone su propio conjunto de certificados de CA, de modo que no usa el
  almacén de confianza del sistema operativo. Un extremo de Slack o un proxy de interceptación con un
  certificado privado falla la verificación salvo que el certificado se añada a ese conjunto.
- El conector no tiene opción de proxy. El cliente de Slack lee `HTTPS_PROXY`, `https_proxy`,
  `HTTP_PROXY` y `http_proxy` del entorno del usuario que ejecuta el comando, así que defínalas en el
  entorno del servicio si el servidor necesita un proxy.

## Resolución de problemas

El conector informa de la mayoría de los fallos en la salida estándar y continúa. Lea el mensaje, no
el código de salida.

| Síntoma | Causa y acción |
| --- | --- |
| `Got an Slack auth error: invalid_auth` | El token es incorrecto o está revocado, o no es un token de bot; una URL de Incoming Webhook no puede autenticar esta llamada. Copie de nuevo el **Bot User OAuth Token** de la aplicación instalada. |
| `Got an Slack auth error: not_in_channel` | La aplicación no es miembro del canal. Invítela con `/invite @<APP_NAME>` o conceda `chat:write.public`. |
| `Got an Slack auth error: channel_not_found` | El identificador o el nombre del canal es incorrecto, o la aplicación no puede ver un canal privado al que no pertenece. |
| `Got an Slack auth error: missing_scope` | A la aplicación le falta `chat:write`. Añada el permiso en **OAuth & Permissions** y reinstale la aplicación: los permisos solo surten efecto tras reinstalar. |
| `Got an Slack auth error: ratelimited` | Demasiados mensajes a ese canal en poco tiempo. Espacie las alertas o quite el mensaje de pie para reducir el tráfico a la mitad. |
| `File Got an error: <error>` (por ejemplo `method_deprecated`) | La carga del gráfico usa el método de Slack retirado el 12 de noviembre de 2025. Quite `--api_conf` y `--module_graph`; el texto de la alerta ya se había entregado. |
| `Warning, error parsing keypairs values: …` y datos que faltan | Un valor de datos contiene `=` o la lista de pares está mal formada. Use valores sin `=` o reestructure el comando de alerta. |
| El canal muestra la alerta pero la ejecución termina con una traza sobre `assert` | Slack reescribió el texto del mensaje y el conector lo compara con el que envió. La entrega se realizó; el fallo es cosmético. |
| `bad interpreter: No such file or directory` | El comando llama directamente al fichero empaquetado y el intérprete declarado dentro de ese fichero no está disponible en el servidor. Llame al conector a través del intérprete instalado en el host o proporcione el nombre declarado. |
| `No such file or directory` con la ruta del conector | La ruta instalada y el comando de alerta no coinciden, normalmente por el sufijo `.py`. Renombre el fichero o edite el comando. |
| Un error de verificación de certificado | CA privada o interceptación TLS: el conector solo confía en su propio conjunto de CA (véase arriba). |
| El registro del servidor anota `exceeded the global alert timeout` | El comando no terminó dentro del tiempo de espera global de alertas configurado. Compruebe la conectividad del servidor con `slack.com` y el estado de Slack. |
| Nada en el canal y nada impreso | La acción no está asociada al módulo, la alerta no se dispara o la línea de comandos nunca se ejecutó. Revise primero el historial de alertas en la consola. |

Si un fallo no deja rastro, ejecute a mano la línea de comandos con los mismos valores que sustituye
la consola y lea la salida. El conector imprime ahí sus propios diagnósticos.

## Referencia

### Parámetros de línea de comandos

| Nombre | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `-d`, `--data` | Sí | — | Datos como pares `clave=valor` separados por comas, por ejemplo `Agent=<AGENT_NAME>,Module=<MODULE_NAME>,Data=22`. Se acepta vacío y no produce líneas de datos. |
| `-t`, `--token` | Sí | — | Token de bot de la aplicación de Slack (`xoxb-…`). Una URL de webhook no es válida aquí. |
| `-c`, `--channel` | Sí | — | Identificador del canal (`C…`, `G…`) o nombre del canal. La aplicación debe ser miembro del canal. |
| `-e`, `--emoji` | No | `:red_circle:` | Emoji que precede a la línea del título. Marcado de emoji de Slack, por ejemplo `:warning:`. |
| `-T`, `--tittle` | No | `PandoraFMS alert` | Línea del título, en negrita. El nombre largo es `--tittle`, con dos `t`. |
| `-D`, `--desc` | No | vacío | Línea de descripción, en cursiva. Vacío deja una línea en cursiva vacía. |
| `-F`, `--footer` | No | `PandoraFMS` | Texto de un segundo mensaje independiente. Un valor vacío (`-F ""`) suprime ese mensaje. |
| `--api_conf` | No | vacío | Datos de la API de Pandora FMS para generar el gráfico: `user=…,pass=…,api_pass=…,api_url=…`. `api_url` toma por defecto `http://127.0.0.1/pandora_console/include/api.php`. Sin `user`, `pass` y `api_pass` se omite la generación del gráfico. |
| `--module_graph` | No | vacío | Petición del gráfico: `module_id=…,interval=…`. `interval` toma por defecto `3600` segundos. Requiere `--api_conf`. |
| `--tmp_dir` | No | `/tmp` | Directorio donde se escribe la imagen del gráfico antes de subirla. |

Con `--api_conf`, la ejecución imprime `Api config enable` antes del mensaje. Los errores de
argumentos —por ejemplo, una opción obligatoria ausente— los informa el analizador de argumentos en la
salida de error y terminan la ejecución con estado `2`.

### Estructura del mensaje

| Línea | Contenido | Origen |
| --- | --- | --- |
| 1 | `<emoji> *<title>*` | `-e` y `-T` |
| 2 | `_<description>_` | `-D` |
| 3 | vacía | — |
| 4… | `*<clave>* : <valor>`, una por par | `-d`, en el orden recibido |
| Mensaje aparte | `<footer>` | `-F`, se omite si está vacío |

### Códigos de salida

| Situación | Estado |
| --- | --- |
| Slack acepta el mensaje | `0` |
| Error de la API de Slack (`invalid_auth`, `not_in_channel`, `missing_scope`, `ratelimited`…) | `0` — el error se imprime y la ejecución termina |
| Error al generar o subir el gráfico | `0` — el texto de la alerta ya se había enviado |
| `SIGINT` o `SIGTERM` | `0` |
| Slack devuelve un texto distinto del enviado | `1` — traza de error, después de la entrega |
| Argumentos de línea de comandos ausentes o no válidos | `2` |

### Objetos de consola incluidos en el producto

| Objeto | Detalle |
| --- | --- |
| Comando de alerta | **Pandora Slack**, no es un comando interno, así que ejecuta el ejecutable en el servidor de alertas |
| Acción de alerta | **Pandora Slack**, incluida como acción predeterminada, con campos de disparo y de recuperación independientes |
| Ruta que espera el comando | `/usr/share/pandora_server/util/plugin/pandora-slack-cli` |
| Nombre del fichero empaquetado | `pandora-slack-cli.py` |
| Entrada en el Marketplace | Ninguna: el conector viene con Pandora FMS |
| Versión publicada | Ninguna: el conector no informa de versión, así que esta página documenta el comportamiento observado el 2026-10-27 |

### Superficie de Slack utilizada

| Método de Slack | Permiso | Uso | Estado actual |
| --- | --- | --- | --- |
| `chat.postMessage` | `chat:write` | El mensaje de alerta y el mensaje de pie | Disponible |
| `files.upload` | `files:write` | La imagen del gráfico del módulo | Retirado por Slack el 12 de noviembre de 2025; la carga falla |
