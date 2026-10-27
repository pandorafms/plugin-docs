# Integración con Discord

*Última actualización del artículo: 2026-10-26.*

## Qué hace

Esta integración publica alertas de Pandora FMS en un canal de texto de Discord
mediante un webhook de canal. Cada alerta se convierte en un mensaje de
Discord: un embed con título, descripción, un campo por cada pareja
`clave=valor` que se envíe y, opcionalmente, miniatura, pie de página y el
gráfico del módulo adjunto.

El conector se distribuye con Pandora FMS; no tiene entrada en el Marketplace
ni componente propio en la consola. Es un comando externo que lanza un comando
de alerta estándar de Pandora FMS, de modo que el lado de Pandora FMS de la
integración son el comando de alerta y la acción de alerta que guarda la URL
del webhook. Una ejecución no crea agentes, no genera módulos y no guarda
estado: publica una vez y termina.

El destino es un webhook, no un bot. El conector escribe en un canal y no lee
nada de Discord.

## Preparación de Discord

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Conector de Discord distribuido con Pandora FMS | Objetivo documentado | Conector que describe esta página. No tiene entrada en el Marketplace y no declara versión. Consulte [Identidad del conector](#identidad-del-conector) |
| Un canal de texto de Discord con un webhook de canal | `Requerido` | Cada ejecución publica en una única URL de webhook |
| Acceso HTTPS desde el host que ejecuta el conector hasta `discord.com` (TCP `443`) | `Requerido` | La alerta se entrega como una petición POST HTTPS a la URL del webhook |
| Un intérprete `python3` y las librerías que declara el `requirements.txt` del conector | `Requerido` | La definición de comando incluida invoca `python3 pandora_discord_cli.py`, y el conector carga esas librerías al arrancar |
| Versión de Pandora FMS | `Sin validar` | No existe un registro de validación por versión para este conector |
| Versión de la API de Discord | `Sin validar` | No hay ninguna versión de la API de webhooks de Discord registrada para este conector |
| Sistema operativo del servidor de Pandora FMS | `Sin validar` | No hay sistema operativo registrado para este conector |

### Requisitos

1. Una cuenta de Discord que pueda gestionar webhooks en el canal de destino:
   el permiso **Manage Webhooks** sobre ese canal.
2. Un canal de texto que reciba las alertas. Un canal dedicado mantiene el
   tráfico de alertas aparte y permite restringir quién lo lee.
3. Acceso de red desde el host que ejecuta el conector hasta `discord.com` en
   el puerto TCP `443`.
4. El directorio del conector en el servidor de Pandora FMS, con sus librerías
   instaladas y con permiso de lectura y ejecución para el usuario con el que
   se ejecuta el servidor de Pandora FMS.
5. La URL del webhook, guardada como un secreto (consulte
   [Crear el webhook](#crear-el-webhook)).

### Crear el webhook

Cree un webhook para el canal que recibirá las alertas:

1. Abra el canal de texto de destino y su configuración.
2. Abra **Integrations** y cree un webhook para ese canal.
3. Asígnele un nombre y, si lo desea, un avatar. Es la identidad que verán los
   miembros del canal como remitente de cada alerta.
4. Copie la URL del webhook y guarde el webhook.

<!-- SCREENSHOT NEEDED: Discord channel settings, Integrations view with the created channel webhook and the Copy Webhook URL action -->

La URL tiene la forma
`https://discord.com/api/webhooks/<WEBHOOK_ID>/<WEBHOOK_TOKEN>` y es la única
credencial que usa el conector: publicar no requiere ninguna otra
autenticación. Cualquiera que tenga esa URL puede publicar en el canal, así que
trátela como un secreto y cree un webhook nuevo si se filtra. Si elimina el
webhook en Discord, la URL deja de ser válida de inmediato.

Un webhook no es un bot: solo puede publicar en su propio canal y nada más. No
puede leer mensajes, listar canales ni reaccionar.

## Configuración de Pandora FMS

### Instalar el conector

Descomprima el paquete del conector en el servidor de Pandora FMS. La
definición de comando que se distribuye con el paquete lo espera en
`/usr/share/pandora_server/util/pandora-discord`, y los ejemplos de esta página
usan esa ruta; cualquier otro directorio sirve siempre que el servidor de
Pandora FMS pueda leerlo y ejecutarlo. Instale sus librerías desde ese
directorio:

```bash
cd /usr/share/pandora_server/util/pandora-discord
pip3 install -r requirements.txt
```

### Crear el comando de alerta

Vaya a **Alerts** → **Commands** → **Create**. El comando es una línea de
órdenes de texto libre, y la consola sustituye `_field1_` … `_field20_` por los
valores de la alerta antes de ejecutarla. Pegue la definición incluida en el
archivo `test-exec.txt` del conector:

```bash
python3 /usr/share/pandora_server/util/pandora-discord/pandora_discord_cli.py -u "_field1_" -d "_field2_" -D "_field3_" --tittle_color _field4_ --thumb _field5_ --api_conf "_field6_" --module_graph "_field7_" -A "Pandora FMS Alert system" --footer "PandoraFMS" --author_icon_url "https://pandorafms.com/wp-content/uploads/2019/04/software-de-monitorizacion-pandorafms-logo.png" --author_url https://pandorafms.com/ --tmp_dir /tmp
```

El comando usa siete campos. Describa cada uno en el comando: la descripción es
la etiqueta que la acción de alerta muestra junto al campo.

| Campo | Valor en la ejecución | Oculto |
| --- | --- | --- |
| `_field1_` | URL del webhook de Discord | Sí |
| `_field2_` | Datos de la alerta como parejas `clave=valor` separadas por comas | No |
| `_field3_` | Descripción del embed (`-D`) | No |
| `_field4_` | Color del título del embed: seis dígitos hexadecimales (`-T`) | No |
| `_field5_` | URL de la miniatura (`--thumb`) | No |
| `_field6_` | Datos de la API de la consola para generar el gráfico del módulo (`--api_conf`) | Sí |
| `_field7_` | Datos del gráfico del módulo (`--module_graph`) | No |

Marque **Hide** en Field 1 para que la URL del webhook se enmascare al editar
la acción, y también en Field 6 si coloca credenciales de la consola ahí. La
marca de oculto solo enmascara el valor en pantalla; no cifra nada.

El formulario muestra tantas filas de campos como permita el ajuste
`max_macro_fields` de la consola (10 por defecto, 20 como máximo). Este comando
necesita siete. El formulario tiene además una columna **Field N values**: para
este comando esos valores se ignoran, porque lo que recibe el conector procede
de la acción de alerta.

El resto de opciones de la línea (autor, pie de página, icono y enlace del
autor, directorio temporal) son constantes del comando. Edite la línea de
órdenes si necesita otros valores.

<!-- SCREENSHOT NEEDED: Alerts > Commands > Create form with the Discord command line and the seven field descriptions -->

Guarde el comando con un nombre y un grupo.

### Crear la acción de alerta

Vaya a **Alerts** → **Actions** → **Create** y seleccione el comando que acaba
de crear. El formulario muestra una pareja de valores por cada campo que
declara el comando. Rellene los valores de disparo:

| Campo | Ejemplo |
| --- | --- |
| Field 1 | `<DISCORD_WEBHOOK_URL>` |
| Field 2 | `Agent=_agent_,Module=_module_,Status=_alert_text_severity_,Data=_data_,Timestamp=_timestamp_` |
| Field 3 | `Alert on _agent_` |
| Field 4 | `ed2512` |
| Field 5 | No lo rellene si no quiere miniatura |
| Field 6 | `user=<USERNAME>,pass=<PASSWORD>,api_pass=<API_TOKEN>,api_url=<PANDORA_FMS_URL>/pandora_console/include/api.php` |
| Field 7 | `module_id=_id_module_,interval=3600` |

El campo 2 es la carga útil de la alerta: cada pareja se convierte en un campo
del embed. La consola expande las macros de alerta dentro de cada valor de
campo, de modo que `_agent_`, `_module_`, `_data_`, `_alert_text_severity_` y
`_timestamp_` se sustituyen por los valores de la alerta que se disparó.

El campo 4 no tiene un valor por defecto utilizable a través de este comando:
el comando pasa su valor aunque el campo esté vacío, y un valor vacío detiene
la ejecución con un error antes de enviar nada. Use seis dígitos hexadecimales
sin `#`; la forma abreviada de tres dígitos se interpreta como otro color.

Deje el campo 5 vacío salvo que quiera una miniatura. Deje los campos 6 y 7
vacíos si no quiere el gráfico del módulo.

<!-- SCREENSHOT NEEDED: Alerts > Actions > Create form for the Discord action, with the seven value rows -->

Establezca un valor de recuperación para el campo 2 si quiere una carga útil
distinta en los eventos de recuperación. Cuando un campo de recuperación queda
vacío, la consola antepone `[RECOVER]` al valor de los campos 2 a 20, así que
la primera pareja de la cadena de datos llega como `[RECOVER]Agent`.

### Aplicar la acción

Dé a la acción un nombre y un grupo y guárdela con **Create**. Para que se
ejecute, asígnela mediante una plantilla de alerta a los módulos o a la
política que quiera monitorizar, o añádala a las alertas de un módulo.

## Verificación

1. Ejecute el conector a mano desde el servidor de Pandora FMS, sin el
   gráfico:

```bash
python3 /usr/share/pandora_server/util/pandora-discord/pandora_discord_cli.py \
  -u "<DISCORD_WEBHOOK_URL>" \
  -d "Agent=<AGENT_NAME>,Module=<MODULE_NAME>,Status=CRITICAL,Data=22"
```

Salida esperada:

```text
To get graph data api conf shoul be provided please set an api config
Error status code: 204
```

La primera línea se imprime en toda ejecución que no reciba `--api_conf`. La
segunda informa del estado HTTP con el que respondió Discord: `Message sent.
status code: 200` cuando respondió `200`, y `Error status code: <código>` para
cualquier otro estado. Discord acepta una publicación de webhook con `204 No
Content`, así que un mensaje aceptado normalmente imprime la forma `Error
status code: 204`. Confirme el mensaje en el canal.

2. Abra el canal de Discord. El mensaje procede de la identidad del webhook,
   con un embed titulado `Pandora FMS alert fired`, la descripción `alert`, los
   cuatro campos de la cadena de datos y una marca de tiempo con la hora de la
   ejecución.

<!-- SCREENSHOT NEEDED: Discord channel with one alert message, showing the embed and its fields -->

3. Dispare la alerta desde Pandora FMS: fuerce el módulo al estado que vigila
   la acción, o use la plantilla de alerta en la que asignó la acción, y
   confirme que el mismo mensaje llega al canal.

## Entender la integración

### Cómo llega una alerta a Discord

1. La alerta se dispara y la consola construye el comando, sustituyendo cada
   `_fieldN_` por el valor del mismo campo en la acción de alerta, después de
   expandir las macros de alerta que contenga.
2. El servidor de Pandora FMS ejecuta el comando resultante con el usuario con
   el que se ejecuta.
3. El conector compone un mensaje de webhook y lo publica una vez en la URL.
4. Discord publica el mensaje en el canal con la identidad del webhook.
5. El conector imprime la línea de estado y termina.

### Dónde acaba cada opción

| Parte del mensaje | La define |
| --- | --- |
| Nombre y avatar del remitente | La configuración del webhook en Discord. `--avatar_url` sustituye el avatar en ese mensaje |
| Texto plano sobre el embed | `-m`, `--message`. Vacío por defecto |
| Título del embed | `-t`, `--alert_tittle`. Por defecto `PandoraFMS alert fired` |
| Descripción del embed | `-D`, `--alert_desc`. Por defecto `alert` |
| Barra de color del embed | `-T`, `--tittle_color`. Por defecto `53e514` |
| Línea de autor del embed | `-A`, `--author`, con `--author_url` y `--author_icon_url` |
| Miniatura | `--thumb`. Se omite si está vacía |
| Pie de página | `-F`, `--footer`. Se omite si está vacío |
| Marca de tiempo | Siempre el momento de la ejecución. No hay opción |
| Campos | Uno por cada pareja `clave=valor` de `-d`, en el orden en que se escriben |
| Imagen | El gráfico del módulo, cuando `--api_conf` y `--module_graph` están ambos definidos |

El autor del embed no es el remitente. El remitente es la identidad del webhook
en Discord; `-A` solo rellena la línea de autor dentro del embed.

### Cómo se interpretan los datos

`-d` se divide por comas y cada trozo por el signo igual, con los espacios
recortados alrededor de la clave y del valor.

- Un trozo sin signo igual detiene el análisis: la ejecución imprime
  `Warning, error parsing keypairs values: …`, conserva las parejas ya leídas y
  descarta el resto. Lo provocan tanto un valor que contiene un signo igual,
  como `Data=a=b`, como un valor sustituido con una coma, como el nombre de un
  agente.
- Un valor vacío produce un campo vacío en el embed, y Discord rechaza el
  mensaje completo con `400`.
- Los campos se envían tal como llegan: el conector no los recorta, no los
  escapa y no los reordena.

### Código de estado

| Código | Cuándo |
| --- | --- |
| `0` | La petición POST recibió cualquier estado HTTP, incluidos `4xx` y `429`. También cuando la ejecución se interrumpe con `Ctrl-C` o `SIGTERM` |
| `1` | Un error no controlado antes o durante la petición POST: un color que no es hexadecimal, una URL de webhook vacía o mal formada, o un fallo de DNS, TCP o TLS |
| `2` | Error de uso: falta `-d` o `-u`, o hay una opción desconocida |

**El código de estado no informa de la entrega.** Lea la línea de estado
impresa y confirme el mensaje en el canal.

## Operación

- **Ejecución manual.** Ejecute el mismo comando que lanza el comando de
  alerta, desde el servidor de Pandora FMS o desde cualquier host que alcance
  `discord.com`. Es también la forma más rápida de probar un webhook antes de
  crear la acción.
- **Un intento por ejecución.** El conector publica una vez y no reintenta. Un
  `429` o un `5xx` pierden esa alerta.
- **Límite de frecuencia.** Discord limita la frecuencia con la que puede
  publicar un webhook. Una ráfaga de alertas puede ser rechazada; no se encola
  nada localmente.
- **Descarga del gráfico.** La petición que hace el conector a la API de la
  consola para generar el gráfico del módulo no tiene tiempo de espera. Si esa
  API deja de responder, la ejecución queda abierta hasta que la termine el
  tiempo de espera global del sistema de alertas.
- **Archivo temporal.** El gráfico se escribe en `--tmp_dir` (`/tmp` por
  defecto) como `graph_<MODULE_ID>.<EPOCH>.png` y se elimina al final de la
  ejecución. Dos ejecuciones del mismo módulo en el mismo segundo comparten el
  nombre de archivo.
- **Registro del servidor.** Con verbosidad `8` o superior,
  `pandora_server.log` registra la línea de órdenes completa de la acción,
  incluida la URL del webhook y las credenciales de consola del campo 6.
  Téngalo en cuenta antes de subir la verbosidad para un caso de soporte.
- **Credenciales del gráfico.** La petición a la API de la consola lleva el
  usuario, la contraseña y el api pass en la cadena de consulta, y la URL de la
  API por defecto es `http://127.0.0.1` en texto plano. Apuntar `api_url` a una
  consola remota envía esas credenciales por la red en la URL y las deja en el
  registro de accesos de ese servidor web.

## Resolución de problemas

| Síntoma | Causa y solución |
| --- | --- |
| `To get graph data api conf shoul be provided please set an api config` en cada ejecución | Es normal cuando no se pasa `--api_conf`. El gráfico se omite y la alerta se envía igualmente |
| `Error status code: 204` | El mensaje fue aceptado: Discord responde `204 No Content`. Confírmelo en el canal antes de tratarlo como un fallo |
| `Error status code: 400` | La carga útil fue rechazada: un valor de campo vacío, una pareja vacía, más de 25 campos o un texto por encima de los límites de longitud de Discord. Corrija la cadena de datos |
| `Error status code: 401`, `403` o `404` | La URL del webhook es incorrecta, está truncada o fue revocada. Cópiela de nuevo desde la configuración del canal o recree el webhook |
| `Error status code: 429` | Discord está limitando la frecuencia del webhook. La alerta se pierde: el conector no reintenta |
| Un rastro de error que acaba en `invalid literal for int() with base 16` | El campo 4 está vacío o contiene algo que no son dígitos hexadecimales. Use seis dígitos sin `#` |
| Un rastro de error que acaba en `MissingSchema` o en un error de conexión | La URL del webhook está vacía o mal formada, o no se alcanza `discord.com`: DNS, proxy, TCP `443` o TLS |
| `usage: … error: the following arguments are required: -d/--data, -u/--url` | La línea de órdenes perdió una de sus opciones, normalmente porque el comando se editó o se eliminó un campo. Restaure la definición de `test-exec.txt` |
| `Warning, error parsing keypairs values: …` | Una pareja no tiene signo igual, o un valor sustituido contiene una coma o un signo igual. Acorte los valores o elimine el carácter |
| La ejecución termina bien y no aparece nada en Discord | El mensaje fue al canal de otro webhook, o la acción de alerta no está asignada al módulo o a la política que se disparó |
| Aparece el prefijo `[RECOVER]` en el nombre del primer campo | Evento de recuperación con el valor de recuperación del campo 2 vacío. Defina una carga útil de recuperación si no quiere el prefijo |

## Referencia

### Identidad del conector

| Propiedad | Valor |
| --- | --- |
| Nombre | Conector de Discord |
| Distribución | Con Pandora FMS. No tiene entrada en el Marketplace |
| Versión | El conector no la declara |
| Punto de entrada | `pandora_discord_cli.py`, ejecutado con `python3` |
| Archivo de configuración | Ninguno |
| Variables de entorno | Ninguna |
| Componente en la consola | Ninguno. Usa el comando de alerta y la acción de alerta estándar |
| Directorio de instalación del ejemplo incluido | `/usr/share/pandora_server/util/pandora-discord` |

### Parámetros de la línea de comandos

```bash
python3 pandora_discord_cli.py -u <DISCORD_WEBHOOK_URL> -d "<DATA>" [opciones]
```

| Opción | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-u`, `--url` | Sí | — | URL del webhook de Discord, el canal de destino |
| `-d`, `--data` | Sí | — | Parejas `clave=valor` separadas por comas, un campo del embed cada una |
| `-t`, `--alert_tittle` | No | `PandoraFMS alert fired` | Título del embed. La opción se escribe con tres t |
| `-D`, `--alert_desc` | No | `alert` | Descripción del embed |
| `-m`, `--message` | No | Vacío | Texto plano que se envía sobre el embed |
| `-T`, `--tittle_color` | No | `53e514` | Color del embed, hexadecimal sin `#` |
| `-A`, `--author` | No | `PandoraFMS` | Nombre de la línea de autor del embed |
| `-F`, `--footer` | No | Vacío | Texto del pie de página. Se omite si está vacío |
| `--avatar_url` | No | Vacío | Avatar del mensaje, que sustituye al del webhook |
| `--author_url` | No | Vacío | Enlace de la línea de autor del embed |
| `--author_icon_url` | No | Vacío | Icono de la línea de autor del embed |
| `--thumb` | No | Vacío | URL de la miniatura. Se omite si está vacía |
| `--api_conf` | No | — | Datos de la API de la consola para el gráfico del módulo: `user`, `pass`, `api_pass` y, opcionalmente, `api_url` |
| `--module_graph` | No | — | Datos del gráfico: `module_id` y, opcionalmente, `interval`, en segundos (por defecto `3600`) |
| `--tmp_dir` | No | `/tmp` | Directorio de la imagen del gráfico antes de subirla |
| `-h`, `--help` | No | — | Resumen de uso. Su línea de descripción es el texto heredado `Test parser dic` |

`--api_conf` necesita `user`, `pass` y `api_pass`; sin ellos el gráfico se omite
y se informa con un mensaje. `api_url` vale por defecto
`http://127.0.0.1/pandora_console/include/api.php`. `--module_graph` necesita
`module_id`; el gráfico solo se genera cuando están las dos opciones.

### Cadenas de salida

| Salida | Significado |
| --- | --- |
| `Message sent. status code: 200` | La petición POST recibió `200` |
| `Error status code: <código>` | La petición POST recibió cualquier otro estado, incluido el `204` de un mensaje aceptado |
| `Warning, error parsing keypairs values: <error>` | No se pudo analizar una pareja de `-d`; se descarta el resto |
| `Api config enable` | Se pasó `--api_conf` |
| `To get graph data api conf shoul be provided please set an api config` | No se pasó `--api_conf`. Se imprime en toda ejecución sin ella; el gráfico se omite |
| `Error no user defined in api_conf keypairs, skipping graph generation.` | `--api_conf` sin `user`, `pass` o `api_pass`. La alerta se envía igualmente |
| `error no module_id defined in module_graph keypairs, skipping graph generation.` | `--module_graph` sin `module_id` |
| `Graph generated on temporary file <ruta>` | El gráfico se descargó y se guardó |
| `Error requested api url, status code: <código>. skipping graph generation` | La API de la consola rechazó la petición del gráfico |
| `Error, cant generate graph file: <error>` o `Error, cant add graph file: <error>` | No se pudo guardar ni adjuntar el gráfico; la alerta se envía igualmente |
| `Interrupted by user` o `Received SIGTERM signal.` | La ejecución se interrumpió y termina con `0` |

### Límites

| Límite | Valor |
| --- | --- |
| Campos por embed | 25 |
| Longitud del nombre de un campo | 256 caracteres |
| Longitud del valor de un campo | 1024 caracteres |
| Longitud del título del embed | 256 caracteres |
| Longitud de la descripción del embed | 4096 caracteres |
| Longitud del pie de página | 2048 caracteres |
| Longitud del nombre del autor | 256 caracteres |
| Caracteres totales de todos los embeds del mensaje | 6000 |
| Longitud del contenido en texto plano | 2000 caracteres |
| Mensajes por ejecución | 1 |
| Canales por ejecución | 1, el de la URL del webhook |
| Reintentos | Ninguno |
| Adjuntos | La imagen del gráfico del módulo, cuando está habilitada |

El conector no recorta: una alerta por encima de estos límites es rechazada por
Discord con `400`.
