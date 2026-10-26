# Pandora Zendesk

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Pandora Zendesk opera tickets en un sitio de Zendesk Support desde
Pandora FMS. Cada ejecución realiza exactamente una operación contra la API v2
de Zendesk del sitio indicado: leer la lista de tickets, crear un ticket,
actualizar un ticket o eliminar un ticket.

El plugin es un comando de una sola ejecución. No guarda estado, no lee ningún
archivo de configuración, no mantiene conexiones entre ejecuciones y termina
tras una única petición a la API. Su entrada es la línea de comandos: la
operación, el subdominio de Zendesk, un par de credenciales y, en las operaciones
de ticket, los campos del ticket. Su resultado es el cambio realizado en Zendesk;
cuando todo va bien no imprime nada en la salida estándar y nunca genera datos de
módulo para Pandora FMS.

Como el addon no publica valores, trátelo como una acción y no como un
recolector: crea, edita o cierra un ticket dentro de un flujo de trabajo de
Pandora FMS, y el ticket es donde se confirma el resultado. La operación de
lectura consulta la lista de tickets pero descarta la respuesta, así que la
superficie útil de esta versión es la de escritura.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.zendesk`, versión `1.0` | Objetivo documentado | Entrada del Marketplace; consulte [Identidad del addon](#identidad-del-addon) |
| API v2 de Zendesk en `https://<ZENDESK_SUBDOMAIN>.zendesk.com` | `Required` | Todas las peticiones se construyen contra ese host; consulte [Operaciones y endpoints](#operaciones-y-endpoints) |
| Acceso HTTPS desde el host que ejecuta el addon hasta el subdominio de Zendesk, puerto `443` | `Required` | El esquema de la URL está fijado a `https` y el puerto no es configurable |
| Una cuenta de agente de Zendesk y autenticación mediante token de API (o contraseña) | `Required` | En cada ejecución es obligatorio un par de credenciales |
| Un rol de Zendesk que pueda listar, crear, actualizar y eliminar tickets | `Required` | Es un requisito previo de las operaciones que ejecute, no una declaración de compatibilidad |
| Sistema operativo del host que ejecuta el addon | `Not validated` | No hay ningún sistema operativo registrado para esta versión |
| Planes y ediciones de Zendesk | `Not validated` | No hay matriz de planes de Zendesk registrada para este addon |
| Versiones de Pandora FMS | `Not validated` | No hay matriz de versiones registrada. El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |

El addon está publicado en el Marketplace de Pandora FMS, con descarga limitada
a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.zendesk](https://marketplace.pandorafms.com/entries/pandorafms.zendesk)

### Requisitos

1. **Un sitio de Zendesk Support** con el acceso a la API habilitado para la
   cuenta y con el subdominio de ese sitio a mano. El subdominio es la parte
   anterior a `.zendesk.com`: un sitio en `https://example.zendesk.com` tiene el
   subdominio `example`.
2. **Una cuenta de agente de Zendesk dedicada**, con permiso para listar, crear,
   actualizar y eliminar los tickets con los que trabaja el plugin. Una cuenta
   dedicada hace identificable la actividad de Pandora FMS en el historial de
   los tickets y permite revocar su token por separado.
3. **Un par de credenciales**: el correo de la cuenta más un token de API, o
   bien el correo de la cuenta más su contraseña. Consulte
   [Credenciales](#credenciales).
4. **Salida HTTPS** desde el host que ejecuta el addon hasta el subdominio de
   Zendesk. El plugin no ofrece opciones de proxy, de entidad certificadora
   propia, de tiempo de espera ni de puerto, así que la conexión tiene que
   funcionar con los ajustes TLS predeterminados del host.
5. **Una instalación de Pandora FMS** donde registrar y ejecutar el plugin.
   Consulte [Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola).

### Credenciales

El plugin admite dos modos de autenticación y envía las credenciales mediante
autenticación básica HTTP:

| Modo | Opciones | Qué se envía |
| --- | --- | --- |
| Token de API | `-us <EMAIL> -t <API_TOKEN>` | El usuario `<EMAIL>/token` con el token como contraseña |
| Contraseña de la cuenta | `-us <EMAIL> -p <PASSWORD>` | El correo y la contraseña de la cuenta |

Utilice el modo de token de API. Zendesk emite y revoca los tokens por cuenta,
de modo que la credencial se puede rotar sin cambiar la contraseña de la cuenta,
y la autenticación por contraseña hay que habilitarla aparte en Zendesk.

Los dos modos no son excluyentes en el código: pase exactamente uno de `-t` y
`-p`. Cuando están los dos, el plugin envía la petición dos veces, una por modo,
así que una creación genera dos tickets y una actualización se aplica dos veces.
Cuando no hay ninguno, no envía nada y termina con éxito.

El plugin no tiene archivo de credenciales ni lee variables de entorno, así que
la credencial siempre es un argumento de línea de comandos. Por tanto queda
visible en el historial del intérprete de comandos y en la lista de procesos del
host mientras dura la ejecución, y en la consola se guarda en los parámetros del
plugin. Utilice un token dedicado, marque el campo como valor oculto al
registrarlo como plugin de servidor y revoque el token si queda expuesto.
Consulte [Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola).

### Instalar el addon

Descargue el paquete de la entrada del Marketplace y copie el ejecutable
`pandora_zendesk` al host que lo vaya a ejecutar. Para un plugin de servidor, el
directorio recomendado es el de plugins del servidor de Pandora FMS:

```bash
/usr/share/pandora_server/util/plugin/pandora_zendesk
```

Dé permiso de ejecución al archivo para el usuario que ejecuta el servidor de
Pandora FMS. El addon no necesita ningún archivo de configuración asociado: todo
lo que necesita llega por la línea de comandos.

## Configuración

El addon tiene dos superficies de configuración: la línea de comandos, para una
ejecución manual, y el registro como plugin de servidor en la consola, para
ejecutarlo desde Pandora FMS. Ambas pasan las mismas opciones; el registro
únicamente sustituye los valores por macros de la consola.

### Línea de comandos

```text
pandora_zendesk -m <method> -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> [campos del ticket]
```

`-m`, `-i` y `-us` son siempre obligatorios. El resto de opciones depende de la
operación. Para crear un ticket:

```bash
./pandora_zendesk -m post -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> \
    -tn "Fallo de copia de seguridad en el servidor de base de datos" \
    -tb "La copia programada no terminó. Revise el registro del trabajo." \
    -ts new -tp urgent -tt incident
```

Para actualizar el ticket con identificador `19`:

```bash
./pandora_zendesk -m put -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> \
    -id 19 -tn "Fallo de copia de seguridad en el servidor de base de datos" \
    -tb "Se reinició el trabajo de copia." -ts open -tp high -tt incident
```

Para eliminar el ticket con identificador `4`:

```bash
./pandora_zendesk -m delete -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> -id 4
```

Para leer la primera página de tickets:

```bash
./pandora_zendesk -m get -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN>
```

Sustituya `19` y `4` por los identificadores de sus propios tickets. La operación
`get` no imprime nada, contenga lo que contenga el sitio; consulte
[Operaciones](#operaciones).

`-i` acepta solo el subdominio, nunca una URL: un valor con `https://` o con
`.zendesk.com` genera un nombre de host que no existe y la ejecución falla al
resolverlo.

Los campos del ticket se insertan tal cual en el documento JSON que se envía, de
modo que una comilla doble, una barra invertida o un salto de línea dentro de
`-tn`, `-tb`, `-ts`, `-tp` o `-tt` producen un documento que Zendesk rechaza.
Mantenga los valores en una sola línea y sin caracteres de escape, o envíe el
texto desde la interfaz de Zendesk.

En `post` y `put` el plugin envía siempre los cinco campos del ticket. Una opción
que se omita se envía como cadena vacía, que no es un valor válido de ticket, así
que indique todos los campos de la operación: `-tn`, `-tb`, `-ts`, `-tp` y `-tt`.

### Registrar el plugin en la consola

Registrar el addon como plugin de servidor permite que Pandora FMS lo ejecute en
el servidor que corre el módulo, en lugar de hacerlo desde un terminal.

1. Abra **Servidores → Plugins** y registre un plugin nuevo.
2. Indique un nombre y una descripción, y mantenga el tipo de plugin
   **Standard**.
3. En **Comando del plugin**, escriba la ruta absoluta del ejecutable en el
   servidor de Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/pandora_zendesk`.
4. En **Parámetros del plugin**, escriba las opciones con las macros de plugin
   `_field1_`, `_field2_`, ... en el lugar de los valores. Deje la operación fija
   en los parámetros y los datos variables como macros:

```text
-m post -i _field1_ -us _field2_ -t _field3_ -tn _field4_ -tb _field5_ -ts new -tp _field6_ -tt _field7_
```

5. En **Parámetros de macro**, describa cada campo. El ejemplo usa estos
   valores:

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Subdominio de Zendesk, sin esquema y sin `.zendesk.com` | `example` |
| `_field2_` | Correo de la cuenta de Zendesk | `pandora@example.com` |
| `_field3_` | Token de API de esa cuenta; marque **Hide value** | — |
| `_field4_` | Asunto del ticket | `Fallo de copia de seguridad` |
| `_field5_` | Comentario del ticket | `La copia programada no terminó.` |
| `_field6_` | Prioridad del ticket | `urgent` |
| `_field7_` | Tipo de ticket | `incident` |

<!-- SCREENSHOT NEEDED: Formulario de registro de plugin de servidor en la consola de Pandora FMS, con la ruta del comando pandora_zendesk y la línea de parámetros _field1_..._field7_, sin token ni datos de cuenta reales. -->

Registre un plugin por operación, o uno solo cuyos parámetros empiecen por la
operación como macro, porque `-m` y los campos del ticket cambian entre crear,
actualizar y eliminar. Actualizar y eliminar necesitan además `-id`, que es otra
macro cuando el identificador del ticket llega desde el módulo.

Una vez registrado, el plugin está disponible al crear módulos de plugin. Cada
módulo rellena los campos con sus propios valores, así que el mismo registro
sirve para varios flujos de tickets.

<!-- SCREENSHOT NEEDED: Campos de módulo de plugin para el plugin pandora_zendesk registrado, con las macros resueltas a valores por módulo y el campo del token enmascarado. -->

## Verificación

Ejecute el addon manualmente antes de conectarlo a Pandora FMS. Utilice un ticket
que pueda eliminar y confirme el efecto en Zendesk, no en la salida del comando:

1. Cree un ticket con el ejemplo `post` de [Línea de comandos](#linea-de-comandos)
   y anote el código de salida:

    ```bash
    ./pandora_zendesk -m post -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> \
        -tn "Prueba de conectividad de Pandora FMS" \
        -tb "Creado por el addon Pandora Zendesk." \
        -ts new -tp normal -tt question
    echo $?
    ```

2. El comando no imprime nada y `echo $?` devuelve `0`. Esa pareja no demuestra
   que el ticket exista: también es la salida de una petición rechazada.
3. Abra la lista de tickets del sitio en Zendesk y compruebe el ticket nuevo: su
   asunto, comentario, estado, prioridad y tipo tienen que coincidir con las
   opciones enviadas.
4. Elimine el ticket de prueba con el ejemplo `delete` y su identificador, y
   confirme que ya no aparece en la lista de tickets.

Una ejecución correcta no produce salida estándar en ninguna operación:

| Situación | Salida estándar | Código de salida |
| --- | --- | --- |
| Petición aceptada por Zendesk | vacía | `0` |
| Sin `-t` ni `-p` | vacía | `0`, no se envía nada |
| Valor de `-m` distinto de `get`, `post`, `put` o `delete` | vacía | `0`, no se envía nada |
| Zendesk respondió un error con cuerpo JSON (credenciales incorrectas, ticket desconocido, valor de campo no válido) | vacía | `0` |
| Error de transporte, o cuerpo de respuesta que no es JSON | `0` | `1`, con un diagnóstico en la salida de error |

La línea `0` de la última fila es la única salida que el addon escribe por sí
mismo. No es un valor de módulo: es una marca de fallo. Consulte
[Operar y resolver problemas](#operar-y-resolver-problemas).

## Entender los resultados

### Operaciones

| Método | Petición a Zendesk | Efecto |
| --- | --- | --- |
| `get` | `GET /api/v2/tickets` | Lee la primera página de la lista de tickets y la descarta. No imprime nada |
| `post` | `POST /api/v2/tickets` | Crea un ticket con el asunto, el comentario, el estado, la prioridad y el tipo |
| `put` | `PUT /api/v2/tickets/<id>` | Actualiza esos campos del ticket y añade el comentario |
| `delete` | `DELETE /api/v2/tickets/<id>` | Elimina el ticket |

El cuerpo de la respuesta se analiza y nunca se imprime, en todos los métodos. Lo
que el plugin deja es el estado del ticket en Zendesk; lo que devuelve a Pandora
FMS es un código de salida, no datos.

`get` no pagina: Zendesk devuelve la primera página de la lista de tickets y
ofrece las siguientes en `next_page`, que el plugin ignora. Como además descarta
el resultado, `get` solo sirve para comprobar que las credenciales y el nombre
del sitio funcionan a nivel de transporte, y aun eso solo cuando la ejecución
escribe algo en la salida de error.

En `put` el comentario se añade, no se sustituye: cada actualización agrega el
texto de `-tb` al ticket como comentario nuevo, y el plugin no envía el indicador
`public`, así que Zendesk lo registra como respuesta pública al solicitante.

### Qué recibe Pandora FMS

Un módulo de plugin que ejecute este addon no recibe datos de módulo, porque el
addon no emite XML ni ningún valor por la salida estándar. El módulo registra la
ejecución y el ticket en Zendesk es el resultado. No defina umbrales ni gráficas
sobre este módulo: no hay nada que medir.

## Operar y resolver problemas

### Limitaciones conocidas

Son comportamientos de esta versión, no errores de configuración:

- **Todo error es silencioso salvo que falle la propia conexión.** El plugin
  nunca comprueba el estado HTTP. Un `401` por credenciales incorrectas, un `404`
  por un identificador de ticket desconocido y un `422` por un campo no válido
  devuelven un cuerpo JSON de error que se analiza y se descarta, así que la
  ejecución termina con estado `0` y sin mensaje.
- **Con las dos credenciales, la operación se ejecuta dos veces.** `-t` y `-p` se
  tratan como ramas independientes, así que enviar ambas manda dos peticiones.
- **`get` no produce salida** y lee solo la primera página de tickets.
- **Los campos del ticket no se escapan.** Una comilla doble, una barra
  invertida o un salto de línea en un campo del ticket invalida el documento
  JSON y Zendesk lo rechaza, también sin mensaje visible.
- **`put` y `delete` necesitan `-id`.** La opción es opcional en el analizador de
  argumentos, pero sin ella la URL se construye con un identificador vacío y la
  ejecución se detiene con una traza `TypeError` antes de enviar nada.
- **Un valor de `-m` no admitido no hace nada.** Cualquier valor distinto de
  `get`, `post`, `put` o `delete`, incluida una combinación de mayúsculas y
  minúsculas como `Get`, termina con estado `0` sin enviar ninguna petición. La
  ayuda integrada describe `-m` como «get or post», aunque `put` y `delete`
  también están admitidos.
- **La ruta de diagnóstico repite la petición.** Cuando una petición lanza una
  excepción, el manejador de error vuelve a emitirla para construir su mensaje,
  y en las ramas `put` y `delete` usa un método distinto del que falló. Por eso
  el diagnóstico impreso puede describir una segunda llamada, y un segundo `post`
  puede duplicar un ticket que ya se había creado.

### Fallos habituales

| Síntoma | Causa | Qué hacer |
| --- | --- | --- |
| La ejecución no imprime nada y devuelve `0`, pero el ticket no cambió | Zendesk rechazó la petición con un error JSON: credenciales, permisos, identificador de ticket o valor de campo | Revise la cuenta, el token, el identificador y los cinco campos del ticket; confirme el efecto en Zendesk después de cada ejecución |
| `0` en la salida estándar y una traza | La petición lanzó una excepción y el reintento dentro del manejador de error la volvió a lanzar | Compruebe la resolución DNS y el acceso HTTPS a `<ZENDESK_SUBDOMAIN>.zendesk.com` desde ese host |
| `0` en la salida estándar y `Error requesting <Response [<código>]>, please check conectivity` | El cuerpo de la respuesta no era JSON, así que el primer intento falló al analizarlo; el reintento devolvió una respuesta | Lea el código de estado del mensaje: es la respuesta de la petición reintentada |
| `TypeError: can only concatenate str (not "NoneType") to str` | `put` o `delete` sin `-id` | Añada `-id` con el identificador del ticket |
| Dos tickets idénticos tras un `post` | Se enviaron `-t` y `-p` a la vez | Deje exactamente una opción de credencial |
| El ticket se crea pero el comentario está vacío, o la actualización se rechaza | Algún campo del ticket contiene una comilla doble, una barra invertida o un salto de línea, o se omitió alguno de los cinco campos y se envió vacío | Envíe los cinco campos en una sola línea y sin caracteres de escape |
| `Name or service not known`, o un nombre de host que contiene `.zendesk.com` dos veces | `-i` recibió una URL o un nombre de host completo en lugar del subdominio | Pase solo el subdominio |

## Referencia

### Parámetros de línea de comandos

El addon no tiene archivo de configuración ni lee variables de entorno. Todos los
parámetros son opciones de línea de comandos, y cada opción tiene un alias largo.

| Nombre | Alias | Obligatorio | Predeterminado | Descripción |
| --- | --- | --- | --- | --- |
| `-m` | `--method` | Sí | — | Operación: `get`, `post`, `put` o `delete`. El valor se compara literalmente, así que las formas admitidas son `get`, `GET`, `post`, `POST`, `put`, `PUT`, `delete` y `DELETE`. Cualquier otro valor no envía nada y termina con `0` |
| `-i` | `--ip` | Sí | — | Subdominio del sitio de Zendesk, sin esquema y sin `.zendesk.com`. El host se construye como `https://<valor>.zendesk.com` |
| `-us` | `--user` | Sí | — | Correo de la cuenta de Zendesk |
| `-t` | `--token` | Uno de `-t` o `-p` | — | Token de API. Se envía como contraseña del usuario `<EMAIL>/token` |
| `-p` | `--password` | Uno de `-t` o `-p` | — | Contraseña de la cuenta, enviada con el correo en autenticación básica HTTP |
| `-tn` | `--ticketname` | `post` y `put` | Cadena vacía | Asunto del ticket |
| `-tb` | `--ticketbody` | `post` y `put` | Cadena vacía | Comentario del ticket. En `put` se añade como comentario nuevo |
| `-id` | `--idticket` | `put` y `delete` | — | Identificador del ticket que se actualiza o se elimina. Omitirlo detiene la ejecución con una traza |
| `-ts` | `--ticketstatus` | `post` y `put` | Cadena vacía | Estado del ticket. La ayuda integrada lo describe como «ticket body» |
| `-tp` | `--ticketpriority` | `post` y `put` | Cadena vacía | Prioridad del ticket. La ayuda integrada lo describe como «ticket body» |
| `-tt` | `--tickettype` | `post` y `put` | Cadena vacía | Tipo de ticket. La ayuda integrada lo describe como «ticket body» |

`-h` y `--help` imprimen el resumen de uso y terminan con `0`.

### Operaciones y endpoints

Todas las peticiones se envían a `https://<ZENDESK_SUBDOMAIN>.zendesk.com`, con
las cabeceras `Accept: application/json` y `Content-Type: application/json`.

| Método | Endpoint | Cuerpo |
| --- | --- | --- |
| `get` | `GET /api/v2/tickets` | Ninguno |
| `post` | `POST /api/v2/tickets` | `{"ticket": {"subject", "comment": {"body"}, "status", "priority", "type"}}` |
| `put` | `PUT /api/v2/tickets/<id>` | `{"ticket": {"subject", "comment": {"body"}, "status", "priority", "type"}}` |
| `delete` | `DELETE /api/v2/tickets/<id>` | Ninguno |

El cuerpo se arma por concatenación, sin escapar los valores de los campos del
ticket.

### Valores de ticket

El plugin no valida estos valores: los envía tal como los recibe y es Zendesk
quien decide si los acepta. Los valores publicados para este addon son:

| Campo | Opción | Valores admitidos |
| --- | --- | --- |
| Estado | `-ts` | `new`, `open`, `hold`, `pending`, `solved`, `closed` |
| Prioridad | `-tp` | `urgent`, `high`, `normal`, `low` |
| Tipo | `-tt` | `problem`, `incident`, `question`, `task` |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.zendesk` |
| Nombre | Pandora Zendesk |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2025-06-26 |
| Archivo distribuido | `pandorafms.zendesk.1.0.zip` |
| Categoría | Miscelaneus |
| Licencia | One |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Autor | Pandora FMS |
| Descargas | 3 |
