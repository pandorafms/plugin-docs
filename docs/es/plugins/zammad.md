# Pandora Zammad

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Pandora Zammad gestiona tickets de Zammad desde la línea de comandos.
Cada ejecución realiza una operación contra la API REST de Zammad: leer la
lista de tickets, crear un ticket, actualizar un ticket o eliminar un ticket.
Es un comando autónomo: no crea agentes, no genera módulos de Pandora FMS y no
guarda estado entre ejecuciones.

El addon se dirige a la cuenta de Zammad Cloud de un subdominio. El endpoint se
construye con el valor de `-i`, que es únicamente la etiqueta del subdominio:

```text
https://<ZAMMAD_SUBDOMAIN>.zammad.com/api/v1/tickets
```

`put` y `delete` añaden el identificador del ticket a esa ruta. Todas las
peticiones y respuestas son JSON sobre HTTPS.

Una ejecución correcta no imprime nada. El comando no devuelve datos a quien
lo invoca: el único resultado es el código de estado, y un rechazo de Zammad no
siempre lo modifica (consulte [Código de estado](#codigo-de-estado)). El efecto
de la operación solo se ve en Zammad.

El addon no es un plugin de servidor ni un plugin de agente de Pandora FMS: una
ejecución no produce XML de agente ni valor de módulo, así que Pandora FMS no
ingiere nada de ella.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.zammad`, versión `1.0` | Objetivo documentado | El paquete del Marketplace que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Acceso HTTPS desde la máquina que ejecuta el addon a `<ZAMMAD_SUBDOMAIN>.zammad.com` (TCP `443`) | `Requerido` | Todas las peticiones van a esa dirección; el addon no permite cambiar el esquema, el dominio ni el puerto |
| Un usuario o un token de Zammad con permiso para leer y escribir tickets | `Requerido` | El addon se autentica con las credenciales que recibe y no comprueba permisos por sí mismo |
| Una cuenta de Zammad Cloud direccionada como `<nombre>.zammad.com` | `Requerido` | El endpoint siempre es `https://<valor de -i>.zammad.com` |
| Versiones de Zammad | `Sin validar` | No se ha registrado una matriz de versiones de Zammad para este addon |
| Sistema operativo de la máquina que ejecuta el addon | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |

**Alcance de la dirección.** La URL está fijada a
`https://<valor de -i>.zammad.com/api/v1/tickets`, así que `-i` es una etiqueta
de subdominio, no una URL. Una instalación propia de Zammad servida desde otro
dominio, sobre HTTP sin cifrar o en un puerto distinto queda fuera de esta
interfaz: el addon no se puede dirigir a ella.

### Requisitos

1. **Acceso de red** desde la máquina que ejecuta el addon a
   `https://<ZAMMAD_SUBDOMAIN>.zammad.com` por TCP `443`.
2. **Una cuenta de Zammad con acceso a la API** y un método de credenciales:
   un token de acceso, o un usuario y una contraseña cuando la instancia
   mantiene habilitada la autenticación básica.
3. **Permiso sobre tickets para esa identidad.** Debe poder leer, crear,
   actualizar y eliminar los tickets sobre los que se opera. El addon envía la
   petición y no inspecciona la respuesta.
4. **Valores que existan en la instancia**: el nombre del grupo del ticket, los
   identificadores numéricos de prioridad y estado, el tipo de artículo y el
   cliente. El addon no los valida; Zammad acepta o rechaza cada petición.

### Acceso a Zammad

Zammad admite autenticación por token y autenticación básica HTTP, y cualquiera
de las dos puede estar deshabilitada en una instancia. El addon implementa
ambas:

- **Token de acceso** (`-t`): se envía en la cabecera
  `Authorization: Token token=<API_TOKEN>`. Zammad recomienda el token frente a
  la autenticación básica, y el token actúa con los permisos del usuario que lo
  creó.
- **Usuario y contraseña** (`-us` y `-p`): se envían como autenticación básica
  HTTP.

Use exactamente un método de credenciales. Con los dos, el addon envía la
petición dos veces (consulte [Credenciales y transporte](#credenciales-y-transporte)).

La identidad debe poder trabajar con tickets del grupo de destino, porque las
peticiones no llevan ninguna otra identidad.

### Instalar el addon

Descargue `pandorafms.zammad.1.0.zip` de la entrada del Marketplace, que está
limitada a usuarios con licencia, y coloque el ejecutable `pandora_zammad` en
la máquina que lo va a ejecutar:

[https://marketplace.pandorafms.com/entries/pandorafms.zammad](https://marketplace.pandorafms.com/entries/pandorafms.zammad)

Los ejemplos de esta página ejecutan el ejecutable desde su propio directorio como
`./pandora_zammad`. El addon no tiene componente de consola: no se añade nada a
la consola de Pandora FMS y la máquina solo tiene que alcanzar la API de Zammad.

## Configuración

Cada ejecución recibe la operación, el subdominio de Zammad y un método de
credenciales como argumentos:

```bash
./pandora_zammad -m <METHOD> -i <ZAMMAD_SUBDOMAIN> [-t <API_TOKEN> | -us <USERNAME> -p <PASSWORD>]
```

El addon no tiene fichero de configuración y no lee ninguna variable de
entorno: todos los valores, incluidas las credenciales, son argumentos de la
línea de comandos. El método se compara sin distinguir mayúsculas.

### Métodos

| Valor de `-m` | Petición | Efecto |
| --- | --- | --- |
| `get` | `GET https://<ZAMMAD_SUBDOMAIN>.zammad.com/api/v1/tickets` | Lee la lista de tickets. La respuesta se descarta |
| `post` | `POST` en el mismo endpoint | Crea un ticket con los campos del ticket y un artículo |
| `put` | `PUT .../tickets/<TICKET_ID>` | Envía los mismos campos a un ticket existente |
| `delete` | `DELETE .../tickets/<TICKET_ID>` | Elimina el ticket |

Un valor distinto de estos cuatro no envía ninguna petición y termina con
código `0` sin salida.

### Crear un ticket

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> \
    -tn "Impresora sin conexión en la planta 2" -tg Users -tp 2 -ts 1 \
    -tt note -tsub "Impresora sin conexión" \
    -tb "La impresora no responde en la red." \
    -tc <CUSTOMER_EMAIL> -tnote "Creado por Pandora FMS"
```

Todos los indicadores de campos del ticket de este comando son necesarios en la
práctica: una creación o una actualización a la que le falta uno no envía la
petición y termina con un error (consulte
[Parámetros de la línea de comandos](#parametros-de-la-linea-de-comandos)). El
addon no valida los valores; los valida Zammad.

La misma creación con autenticación básica en lugar de token:

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -us <USERNAME> -p <PASSWORD> \
    -tn "Impresora sin conexión en la planta 2" -tg Users -tp 2 -ts 1 \
    -tt note -tsub "Impresora sin conexión" \
    -tb "La impresora no responde en la red." \
    -tc <CUSTOMER_EMAIL> -tnote "Creado por Pandora FMS"
```

### Actualizar un ticket

`put` añade el identificador del ticket al endpoint y envía el mismo cuerpo que
`post`:

```bash
./pandora_zammad -m put -id <TICKET_ID> -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> \
    -tn "Impresora sin conexión en la planta 2" -tg Users -tp 2 -ts 4 \
    -tt note -tsub "Escalado" \
    -tb "El equipo de instalaciones ha sustituido la impresora." \
    -tc <CUSTOMER_EMAIL> -tnote "Actualizado por Pandora FMS"
```

### Eliminar un ticket

`delete` necesita el identificador del ticket y un método de credenciales. Los
indicadores de campos del ticket no se usan en este método:

```bash
./pandora_zammad -m delete -id <TICKET_ID> -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN>
```

### Credenciales y transporte

- Las credenciales son argumentos de la línea de comandos, así que el historial
  del intérprete las conserva y la lista de procesos del sistema operativo las
  expone mientras el comando se ejecuta. Use una identidad de Zammad dedicada y
  proteja con permisos de fichero cualquier script o entrada de `cron` que
  guarde el comando.
- **No pase `-t` y `-p` a la vez.** El addon ejecuta las dos ramas de
  autenticación, así que la petición se envía dos veces: un `post` crea dos
  tickets y un `delete` encadena a la primera eliminación una segunda petición
  que falla.
- La conexión es siempre HTTPS. El addon no expone ninguna opción TLS: la
  validación del certificado es la predeterminada del cliente contra el
  almacén de confianza del sistema, y no hay ningún indicador para añadir un
  paquete de CA ni para aceptar un certificado no verificado.
- El token viaja en una cabecera, no en la URL, así que no aparece en la línea
  de petición capturada ni en el registro de accesos del servidor.
- Ninguna petición tiene tiempo de espera. Un endpoint que acepta la conexión y
  no responde mantiene la ejecución abierta (consulte
  [Operar y resolver problemas](#operar-y-resolver-problemas)).

## Verificación

Una petición correcta no imprime nada, y el código de estado por sí solo no
demuestra que Zammad haya aceptado la operación. Verifique el efecto en Zammad.

1. **Compruebe la conectividad y la autenticación** con una lectura:

```bash
./pandora_zammad -m get -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN>
echo "exit=$?"
```

Salida esperada: nada en absoluto, y `exit=0`. Un token incorrecto, o un token
sin permiso sobre tickets, tampoco imprime nada y normalmente también termina
con `0`, porque el addon analiza el cuerpo y no evalúa el código HTTP.

2. **Cree un ticket en un grupo de pruebas** y confírmelo en Zammad:

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> \
    -tn "Prueba de conectividad de Pandora FMS" -tg Users -tp 2 -ts 1 \
    -tt note -tsub "Prueba de conectividad" \
    -tb "Ticket de prueba creado para validar el addon." \
    -tc <CUSTOMER_EMAIL> -tnote "Creado por Pandora FMS"
```

Esperado: ninguna salida, código `0` y el ticket con su artículo visible en el
grupo `Users` de Zammad.

3. **Elimine el ticket de prueba** y confirme que ya no está:

```bash
./pandora_zammad -m delete -id <TICKET_ID> -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN>
```

4. **Fuerce la ruta de error** omitiendo un campo del ticket en una creación:

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> -tn "Solo un título"
```

La ejecución se detiene antes de enviar la petición, informa del fallo en la
salida de error y termina con código `1`.

## Entender los resultados

El addon no escribe nunca la respuesta de la API en ningún sitio. Una ejecución
`get` lee la lista de tickets y la descarta, así que el comando no sirve para
listar tickets en una terminal; para eso use la interfaz de Zammad u otro
cliente.

| Valor de `-m` | Qué cambia la ejecución en Zammad |
| --- | --- |
| `post` | Un ticket nuevo con el título, el grupo, la prioridad, el estado, el cliente y la nota, y un artículo con el asunto, el cuerpo y el tipo indicados |
| `put` | Los mismos campos sobre un ticket existente, y un artículo más |
| `delete` | El ticket se elimina. Los indicadores de campos del ticket no se usan |
| `get` | Nada: la respuesta se descarta |

El cuerpo de la petición se compone con los indicadores de
[Cuerpo de la petición](#cuerpo-de-la-peticion). Los indicadores que el método
no usa se aceptan igualmente y no tienen efecto.

**El código de estado no es un informe de éxito.** El addon comprueba si el
cuerpo de la respuesta es JSON, no si Zammad aceptó la petición. Por eso un
`401`, un `403`, un `404` o un `422` respondido con un cuerpo JSON parece un
éxito: sin salida y con código `0`. Solo un cuerpo que no sea JSON válido, o un
fallo de transporte, produce un error.

## Operar y resolver problemas

Cada ejecución es independiente: el comando envía su petición y termina. No hay
demonio, ni caché, ni estado que reiniciar, así que se puede ejecutar a mano,
desde `cron` o desde cualquier superficie de Pandora FMS que ejecute un comando
externo.

- El addon informa del resultado solo mediante el código de estado; la prueba
  es el propio ticket. Cuando el resultado importe, lea el ticket en Zammad
  después de la ejecución.
- La petición no tiene tiempo de espera. Fije un tiempo máximo de ejecución en
  quien invoca el comando (el tiempo de espera de la superficie que lo ejecuta,
  o `timeout(1)`) para que un endpoint mudo no bloquee la planificación.
- Como una petición rechazada termina con `0` igual que una aceptada, un script
  que deba reaccionar a un fallo tiene que comprobar el ticket en Zammad; el
  código de estado no basta.

| Síntoma | Causa y solución |
| --- | --- |
| Sin salida y código `0` | Es lo normal en una petición aceptada, y también en una rechazada. Confirme el efecto en Zammad (consulte [Verificación](#verificacion)) |
| `0` en la salida estándar seguido de `Error requesting <Response [404]>, please check conectivity`, código `1` | La API respondió con un cuerpo que no es JSON válido, normalmente porque `-i` no corresponde a una cuenta de Zammad Cloud o porque un proxy devolvió una página de error. Compruebe el subdominio |
| Un error no controlado que nombra una petición fallida, código `1` | El reintento interno del tratamiento de errores también falló, así que la API no es alcanzable: DNS, TCP `443`, TLS o un cortafuegos |
| Un error no controlado antes de enviar ninguna petición, código `1` | Falta un campo del ticket en `post` o `put`, o falta `-id` en `put` o `delete`. Añada todos los valores que necesita el cuerpo |
| Aparecen dos tickets, o la operación se aplica dos veces | Se pasaron `-t` y `-p` a la vez. Use exactamente un método de credenciales |
| No se envía ninguna petición y el comando termina con `0` | No se pasó `-t` ni `-p`, o `-m` tiene un valor distinto de `get`, `post`, `put` y `delete` |
| Un error de uso que enumera los argumentos necesarios, código `2` | Falta `-m` o `-i`, o un indicador está mal escrito |
| Zammad rechaza el ticket y el comando termina igualmente con `0` | El token o el usuario no tiene permiso sobre tickets, el token es incorrecto o un valor no existe en la instancia. El addon no informa del código HTTP |
| La petición se rechaza cuando el texto contiene una comilla doble o un salto de línea | Los valores se insertan en el cuerpo sin escapar, así que ese valor produce una petición no válida. Elimine el carácter del texto |
| Una ejecución no termina nunca | El endpoint aceptó la conexión y no responde, y no hay tiempo de espera. Interrumpa la ejecución y fije un tiempo máximo en quien invoca el comando |

## Referencia

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.zammad` |
| Nombre | Pandora Zammad |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2025-06-26 |
| Categoría | Miscelánea |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Descargas | 2 |
| Entrada del Marketplace | [pandorafms.zammad](https://marketplace.pandorafms.com/entries/pandorafms.zammad) |

### Parámetros de la línea de comandos

```bash
./pandora_zammad -m <METHOD> -i <ZAMMAD_SUBDOMAIN> [options]
```

| Opción | Obligatoria | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `-m`, `--method` | Sí | — | Operación: `get`, `post`, `put` o `delete`, sin distinguir mayúsculas. Otro valor no envía nada y termina con `0` |
| `-i`, `--ip` | Sí | — | Etiqueta del subdominio de Zammad Cloud, no una URL. El endpoint es `https://<valor>.zammad.com/api/v1/tickets`. La ayuda integrada la describe como "zendesk subdomain name" |
| `-t`, `--token` | Condicional | — | Un método de credenciales. Token de acceso de Zammad, enviado como `Authorization: Token token=<valor>` |
| `-us`, `--user` | Condicional | — | Obligatorio con `-p`. Usuario de Zammad para autenticación básica HTTP |
| `-p`, `--password` | Condicional | — | Obligatorio con `-us`. Contraseña de ese usuario |
| `-id`, `--idticket` | Condicional | — | Obligatorio en `put` y `delete`. Identificador del ticket añadido al endpoint |
| `-tn`, `--ticketname` | Condicional | — | Obligatorio en `post` y `put`. Título del ticket |
| `-tg`, `--ticketgroup` | Condicional | — | Obligatorio en `post` y `put`. Nombre del grupo |
| `-tp`, `--ticketpriority` | Condicional | — | Obligatorio en `post` y `put`. Identificador de prioridad |
| `-ts`, `--ticketstatus` | Condicional | — | Obligatorio en `post` y `put`. Identificador de estado |
| `-tt`, `--tickettype` | Condicional | — | Obligatorio en `post` y `put`. Tipo de artículo |
| `-tsub`, `--ticketsubject` | Condicional | — | Obligatorio en `post` y `put`. Asunto del artículo |
| `-tb`, `--ticketbody` | Condicional | — | Obligatorio en `post` y `put`. Cuerpo del artículo |
| `-tc`, `--ticketcustomer` | Condicional | — | Obligatorio en `post` y `put`. Cliente, como la dirección de correo o el identificador que espera Zammad |
| `-tnote`, `--ticketnote` | Condicional | — | Obligatorio en `post` y `put`. Nota, enviada como campo del ticket de primer nivel |
| `-h`, `--help` | No | — | Resumen de uso |

Los indicadores de campos del ticket son opcionales en la línea de comandos
pero necesarios para una creación o una actualización: el cuerpo no se puede
componer sin ellos, así que la ejecución se detiene con un error en lugar de
enviar una petición incompleta. Un `put` o un `delete` sin `-id` se detiene del
mismo modo.

### Cuerpo de la petición

`post` y `put` envían un documento JSON. El método `delete` y el método `get` no
envían cuerpo.

| Indicador | Campo JSON | Notas |
| --- | --- | --- |
| `-tn` | `title` | |
| `-tg` | `group` | |
| `-tp` | `priority_id` | Se envía como cadena |
| `-ts` | `state_id` | Se envía como cadena |
| `-tc` | `customer` | |
| `-tnote` | `note` | Campo del ticket de primer nivel |
| `-tsub` | `article.subject` | |
| `-tb` | `article.body` | |
| `-tt` | `article.type` | |
| — | `article.internal` | Siempre `false`; no hay indicador para cambiarlo |

El cuerpo se envía con `Content-Type: application/json`. Los valores se
insertan tal como llegan, sin escapar, así que una comilla doble o un salto de
línea dentro de un campo del ticket hace que el cuerpo no sea válido.

Solo los campos de esta tabla forman parte de la interfaz: las etiquetas, el
propietario, el tiempo pendiente y los adjuntos no tienen indicador y no se
pueden definir desde el addon.

### Código de estado

| Código | Cuándo |
| --- | --- |
| `0` | La API respondió y el cuerpo era JSON válido, lo que incluye respuestas `4xx` con un cuerpo de error JSON. También las ejecuciones que no envían petición: sin método de credenciales, o con un valor de `-m` distinto de los cuatro métodos |
| `1` | El cuerpo no era JSON válido: el comando imprime `0` y un mensaje `Error requesting ...`. También un error no controlado antes o durante la petición: un campo del ticket ausente, un identificador de ticket ausente o un fallo de conectividad |
| `2` | Error de uso de la línea de comandos: falta `-m` o `-i`, o hay un indicador no reconocido |
